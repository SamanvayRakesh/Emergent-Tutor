"""PayU payment routes — hash generation, success/failure callbacks, S2S webhook, monthly renewal."""
import os
import hashlib
import hmac
import json
import uuid
import asyncio
from datetime import date, datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from core import db, get_current_user, logger

router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────
PAYU_KEY         = os.environ.get("PAYU_MERCHANT_KEY", "").strip()
PAYU_SALT        = os.environ.get("PAYU_MERCHANT_SALT", "").strip()
PAYU_URL         = os.environ.get("PAYU_PAYMENT_URL", "https://secure.payu.in/_payment")
PAYU_COMMAND_URL = os.environ.get("PAYU_COMMAND_URL", "https://secure.payu.in/merchant/postservice.php?form=2")
BASE_URL         = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000")

PLAN_AMOUNTS       = {"starter": "399.00", "pro": "699.00"}
PLAN_NAMES         = {"starter": "Starter", "pro": "Pro"}
PLAN_BONUS_CREDITS = {"starter": 500, "pro": 1000}

# ── Hashing helpers ───────────────────────────────────────────────────────────

def _sha512(value: str) -> str:
    return hashlib.sha512(value.encode("utf-8")).hexdigest()


def _make_payment_hash(
    txnid: str, amount: str, productinfo: str,
    firstname: str, email: str,
    udf1: str = "", udf2: str = "", udf3: str = "", udf4: str = "", udf5: str = "",
    si_details: str | None = None,
) -> str:
    """
    Standard PayU hash:
      SHA512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT)
    For SI mandate, si_details is appended before the salt:
      SHA512(key|...|||||||||si_details|SALT)
    """
    parts = [
        PAYU_KEY, txnid, amount, productinfo, firstname, email,
        udf1, udf2, udf3, udf4, udf5,
        "", "", "", "", "",          # empty additional UDF slots
    ]
    if si_details is not None:
        parts.append(si_details)
    parts.append(PAYU_SALT)
    return _sha512("|".join(parts))


def _verify_response_hash(data: dict) -> bool:
    """
    PayU reverse hash (response verification):
      SHA512(SALT|status|blank|blank|blank|blank|blank|udf5|udf4|udf3|udf2|udf1|
             email|firstname|productinfo|amount|txnid|key)
    """
    parts = [
        PAYU_SALT,
        data.get("status", ""),
        "", "", "", "", "",           # blank additional fields
        data.get("udf5", ""), data.get("udf4", ""), data.get("udf3", ""),
        data.get("udf2", ""), data.get("udf1", ""),
        data.get("email", ""), data.get("firstname", ""),
        data.get("productinfo", ""), data.get("amount", ""),
        data.get("txnid", ""), data.get("key", PAYU_KEY),
    ]
    expected = _sha512("|".join(parts))
    received = data.get("hash", "")
    return bool(received) and hmac.compare_digest(expected, received)


# ── Initiate payment ──────────────────────────────────────────────────────────

class PayUInitiateRequest(BaseModel):
    plan: str   # "starter" or "pro"


@router.post("/payments/payu-initiate")
async def payu_initiate(body: PayUInitiateRequest, request: Request):
    """Generate PayU hash + SI mandate fields. Frontend POSTs these to PayU."""
    user = await get_current_user(request)

    if body.plan not in PLAN_AMOUNTS:
        raise HTTPException(status_code=400, detail="Plan must be 'starter' or 'pro'")
    if not PAYU_KEY or not PAYU_SALT:
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    amount      = PLAN_AMOUNTS[body.plan]
    txnid       = f"ACE-{user['user_id'][-8:]}-{uuid.uuid4().hex[:8]}".upper()
    firstname   = (user.get("name") or "Student").split()[0]
    email       = user.get("email", "student@aceit.in")
    phone       = user.get("phone") or "9999999999"
    productinfo = f"{PLAN_NAMES[body.plan]} Monthly Plan - AceIt AI"

    # SI mandate details for monthly recurring UPI AutoPay
    si_details = json.dumps({
        "billingAmount":    amount,
        "billingCurrency":  "INR",
        "billingCycle":     "MONTHLY",
        "billingInterval":  1,
        "paymentStartDate": date.today().isoformat(),
        "paymentEndDate":   "2099-12-31",
    }, separators=(",", ":"))

    payment_hash = _make_payment_hash(
        txnid, amount, productinfo, firstname, email,
        udf1=body.plan,
        si_details=si_details,
    )

    # Persist pending transaction (idempotent upsert)
    await db.payu_orders.update_one(
        {"txnid": txnid},
        {"$set": {
            "txnid":       txnid,
            "user_id":     user["user_id"],
            "plan":        body.plan,
            "amount":      amount,
            "status":      "initiated",
            "created_at":  datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    fields = {
        "key":        PAYU_KEY,
        "txnid":      txnid,
        "amount":     amount,
        "productinfo": productinfo,
        "firstname":  firstname,
        "email":      email,
        "phone":      phone,
        "surl":       f"{BASE_URL}/api/payments/payu-success",
        "furl":       f"{BASE_URL}/api/payments/payu-failure",
        "hash":       payment_hash,
        "si":         "1",
        "si_details": si_details,
        "udf1":       body.plan,
    }

    return {"action": PAYU_URL, "fields": fields}


# ── Shared callback processor ─────────────────────────────────────────────────

async def _process_payu_callback(data: dict) -> dict:
    """Verify hash, update order, activate plan if successful. Idempotent."""
    txnid = data.get("txnid", "")

    if not _verify_response_hash(data):
        raise HTTPException(status_code=400, detail="Invalid PayU response hash")

    order = await db.payu_orders.find_one({"txnid": txnid})
    if not order:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Amount integrity check
    if str(data.get("amount", "")).strip() != str(order.get("amount", "")).strip():
        raise HTTPException(status_code=400, detail="Amount mismatch — possible tampering")

    status  = data.get("status", "").lower()
    plan_id = data.get("udf1") or order.get("plan", "")

    db_status = "paid" if status == "success" else ("pending" if status == "pending" else "failed")
    update = {
        "status":         db_status,
        "payu_response":  {k: v for k, v in data.items() if k != "_id"},
        "mihpayid":       data.get("mihpayid"),
        "payment_source": data.get("payment_source"),
        "updated_at":     datetime.now(timezone.utc).isoformat(),
    }

    # UPI mandate registered successfully
    if status == "success" and str(data.get("payment_source", "")).upper() == "SIST":
        update["mandate_active"]     = True
        update["mandate_authpayuid"] = data.get("mihpayid")

    await db.payu_orders.update_one({"txnid": txnid}, {"$set": update})

    # Activate subscription plan on success (idempotent)
    if status == "success" and plan_id in PLAN_AMOUNTS:
        bonus = PLAN_BONUS_CREDITS.get(plan_id, 0)
        now   = datetime.now(timezone.utc)
        expires = now + timedelta(days=30)
        is_mandate = str(data.get("payment_source", "")).upper() == "SIST"

        sub_update = {
            "user_id":          order["user_id"],
            "plan":             plan_id,
            "billing_cycle":    "monthly",
            "status":           "active",
            "amount_inr":       float(order["amount"]),
            "started_at":       now.isoformat(),
            "expires_at":       expires.isoformat(),
            "payment_provider": "payu",
            "payment_order_id": txnid,
            "payment_id":       data.get("mihpayid"),
            "updated_at":       now.isoformat(),
        }
        # Store mandate details for monthly renewal
        if is_mandate:
            sub_update["mandate_active"]     = True
            sub_update["mandate_authpayuid"] = data.get("mihpayid")
            sub_update["mandate_seq_no"]     = 1
            sub_update["mandate_email"]      = data.get("email", "")
            sub_update["mandate_phone"]      = data.get("phone", "9999999999")

        await db.subscriptions.update_one(
            {"user_id": order["user_id"]},
            {"$set": sub_update},
            upsert=True,
        )

        if bonus:
            await db.users.update_one(
                {"user_id": order["user_id"]},
                {"$inc": {"credits": bonus}},
            )

        logger.info(f"PayU: activated {plan_id} for user {order['user_id']} txn={txnid} mandate={is_mandate}")

    return {"status": status, "plan": plan_id, "txnid": txnid}


# ── Browser return callbacks ──────────────────────────────────────────────────

@router.post("/payments/payu-success")
async def payu_success(request: Request):
    """PayU posts here after successful payment — verify, activate, redirect to frontend."""
    form = await request.form()
    data = dict(form)
    try:
        result = await _process_payu_callback(data)
        plan   = result.get("plan", "")
        return RedirectResponse(
            f"{BASE_URL}/upgrade?payment=success&plan={plan}",
            status_code=303,
        )
    except Exception as e:
        logger.error(f"PayU success callback error: {e}")
        return RedirectResponse(f"{BASE_URL}/upgrade?payment=failed", status_code=303)


@router.post("/payments/payu-failure")
async def payu_failure(request: Request):
    """PayU posts here after failed / cancelled payment."""
    form = await request.form()
    data = dict(form)
    try:
        await _process_payu_callback(data)
    except Exception as e:
        logger.warning(f"PayU failure callback: {e}")
    return RedirectResponse(f"{BASE_URL}/upgrade?payment=failed", status_code=303)


# ── S2S webhook ───────────────────────────────────────────────────────────────

@router.post("/payments/payu-webhook")
async def payu_webhook(request: Request):
    """PayU server-to-server webhook — same verification, returns JSON (no redirect)."""
    form = await request.form()
    data = dict(form)
    try:
        await _process_payu_callback(data)
    except Exception as e:
        logger.error(f"PayU S2S webhook error: {e}")
    # Always acknowledge to stop PayU retrying
    return {"ok": True}



# ── Monthly renewal job ───────────────────────────────────────────────────────

async def _call_si_transaction(authpayuid: str, amount: str, txnid: str,
                                email: str, phone: str, seq_no: int) -> dict:
    """Call PayU's si_transaction API to charge a recurring mandate."""
    var1 = json.dumps({
        "authpayuid":           authpayuid,
        "amount":               amount,
        "txnid":                txnid,
        "phone":                phone or "9999999999",
        "email":                email,
        "invoiceDisplayNumber": f"INV-{txnid}",
        "mandateSeqNo":         seq_no,
    }, separators=(",", ":"))

    hash_str = _sha512("|".join([PAYU_KEY, "si_transaction", var1, PAYU_SALT]))

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(PAYU_COMMAND_URL, data={
            "form": "2", "key": PAYU_KEY,
            "command": "si_transaction", "var1": var1, "hash": hash_str,
        })
        r.raise_for_status()
        return r.json()


async def _charge_renewal(sub: dict):
    """Attempt one monthly renewal charge for a single subscription."""
    user_id = sub["user_id"]
    plan_id = sub.get("plan", "")
    amount  = PLAN_AMOUNTS.get(plan_id)
    if not amount or not sub.get("mandate_authpayuid"):
        return

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return

    seq_no     = sub.get("mandate_seq_no", 1) + 1
    base_txnid = sub.get("payment_order_id", user_id)
    new_txnid  = f"{base_txnid}-R{seq_no}"

    # Guard against double-processing
    await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {"renewal_processing": True}},
    )
    try:
        result = await _call_si_transaction(
            authpayuid=sub["mandate_authpayuid"],
            amount=amount,
            txnid=new_txnid,
            email=sub.get("mandate_email") or user.get("email", ""),
            phone=sub.get("mandate_phone") or user.get("phone") or "9999999999",
            seq_no=seq_no,
        )

        if result.get("status", "").lower() == "success":
            old_exp = datetime.fromisoformat(sub["expires_at"])
            if old_exp.tzinfo is None:
                old_exp = old_exp.replace(tzinfo=timezone.utc)
            new_exp = old_exp + timedelta(days=30)

            await db.subscriptions.update_one(
                {"user_id": user_id},
                {"$set": {
                    "status":             "active",
                    "expires_at":         new_exp.isoformat(),
                    "mandate_seq_no":     seq_no,
                    "last_renewed_at":    datetime.now(timezone.utc).isoformat(),
                    "renewal_processing": False,
                }},
            )
            logger.info(f"Renewal OK: user={user_id} plan={plan_id} seq={seq_no} expires={new_exp.date()}")
        else:
            await db.subscriptions.update_one(
                {"user_id": user_id},
                {"$set": {
                    "renewal_processing":   False,
                    "last_renewal_attempt": datetime.now(timezone.utc).isoformat(),
                    "last_renewal_status":  result.get("status", "unknown"),
                }},
            )
            logger.warning(f"Renewal failed: user={user_id} result={result}")
    except Exception as e:
        await db.subscriptions.update_one(
            {"user_id": user_id},
            {"$set": {"renewal_processing": False}},
        )
        logger.error(f"Renewal error: user={user_id} error={e}")


async def _run_renewals():
    """Find subscriptions expiring within 24 h (still active, not cancelled) and renew them."""
    if not PAYU_KEY or not PAYU_SALT:
        return
    now    = datetime.now(timezone.utc)
    window = now + timedelta(hours=24)

    cursor = db.subscriptions.find({
        "status":             "active",
        "mandate_active":     True,
        "mandate_authpayuid": {"$exists": True},
        "expires_at":         {"$lte": window.isoformat()},
        "renewal_processing": {"$ne": True},
    })
    async for sub in cursor:
        await _charge_renewal(sub)


async def renewal_scheduler():
    """Background asyncio loop: runs the renewal job once every 24 hours."""
    await asyncio.sleep(60)   # let the app finish starting up first
    while True:
        try:
            logger.info("PayU renewal job: checking due subscriptions...")
            await _run_renewals()
        except Exception as e:
            logger.error(f"Renewal scheduler error: {e}")
        await asyncio.sleep(86400)   # 24 hours
