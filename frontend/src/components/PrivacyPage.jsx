export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-300">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <div className="mb-10">
          <a href="/" className="text-cyan-400 text-sm hover:underline font-body">← Back to AceIt AI</a>
        </div>
        <h1 className="text-4xl font-heading font-black text-white mb-2">Privacy Policy</h1>
        <p className="text-zinc-500 text-sm font-body mb-10">Last updated: July 2026 &nbsp;|&nbsp; Applies to all AceIt AI users</p>

        <div className="space-y-8 font-body text-sm leading-relaxed">

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">1. Introduction</h2>
            <p>AceIt AI ("<strong>we</strong>", "<strong>us</strong>") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, store, and protect your personal information when you use our Platform. By using AceIt AI, you consent to the practices described here.</p>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">2. Information We Collect</h2>
            <p className="mb-2">We collect the following types of information:</p>
            <ul className="list-disc pl-6 space-y-1 text-zinc-400">
              <li><strong className="text-zinc-200">Account data:</strong> Name, email address, school, class level, and password (stored as a secure hash).</li>
              <li><strong className="text-zinc-200">Usage data:</strong> Chat messages, quiz answers, scores, session duration, and feature interactions.</li>
              <li><strong className="text-zinc-200">Progress data:</strong> XP, credits, streaks, quiz history, and adaptive learning profile.</li>
              <li><strong className="text-zinc-200">Device data:</strong> IP address, browser type, and operating system (for security and analytics).</li>
              <li><strong className="text-zinc-200">Payment data:</strong> Transaction IDs and subscription status (payment card details are handled exclusively by Razorpay).</li>
            </ul>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-1 text-zinc-400">
              <li>Providing and improving the Platform services</li>
              <li>Personalising AI tutor responses and adaptive learning</li>
              <li>Processing payments and managing subscriptions</li>
              <li>Sending important service updates and notifications</li>
              <li>Detecting and preventing fraud, abuse, or security threats</li>
              <li>Generating anonymised analytics to improve educational outcomes</li>
              <li>Complying with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">4. AI and Third-Party Data Processing</h2>
            <p className="mb-2">When you use the AI Tutor, your messages are sent to third-party AI providers. Currently we use:</p>
            <ul className="list-disc pl-6 space-y-1 text-zinc-400">
              <li><strong className="text-zinc-200">OpenRouter:</strong> An AI API proxy. Your messages may be processed by models from DeepSeek, OpenAI, or other providers via OpenRouter's infrastructure. See <a href="https://openrouter.ai/privacy" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">OpenRouter Privacy Policy</a>.</li>
              <li><strong className="text-zinc-200">Google (Sign-In):</strong> If you sign in with Google, your Google profile information (name, email, profile photo) is shared with us. See <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">Google Privacy Policy</a>.</li>
              <li><strong className="text-zinc-200">Razorpay (Payments):</strong> Payment processing. See <a href="https://razorpay.com/privacy/" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:underline">Razorpay Privacy Policy</a>.</li>
            </ul>
            <p className="mt-3 text-amber-400">⚠️ Do not share sensitive personal information (passwords, Aadhaar numbers, financial details) in AI chat messages.</p>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">5. Data Storage and Security</h2>
            <p>Your data is stored in secure cloud databases. We implement:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1 text-zinc-400">
              <li>Encrypted storage for all personal data</li>
              <li>Bcrypt hashing for passwords (we never store plaintext passwords)</li>
              <li>HTTPS/TLS for all data transmission</li>
              <li>HTTP-only cookies for session management (not accessible via JavaScript)</li>
              <li>Regular security audits and access controls</li>
            </ul>
            <p className="mt-2">Despite these measures, no system is 100% secure. We cannot guarantee absolute security.</p>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">6. Data Sharing</h2>
            <p>We do not sell your personal data. We share data only:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1 text-zinc-400">
              <li>With your school (administrators can view aggregate performance data for enrolled students)</li>
              <li>With AI providers for generating tutor responses (message content only)</li>
              <li>With Razorpay for payment processing (billing data only)</li>
              <li>When required by law or court order</li>
              <li>In the event of a business merger or acquisition (you will be notified)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">7. Children's Privacy</h2>
            <p>We take children's privacy seriously. For users under 13, we require verifiable parental consent. We do not knowingly collect data from children under 13 without consent. If you believe we have collected data from a child under 13 without consent, contact us immediately for deletion.</p>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">8. Your Rights</h2>
            <p>Under applicable data protection laws, you have the right to:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1 text-zinc-400">
              <li><strong className="text-zinc-200">Access:</strong> Request a copy of data we hold about you</li>
              <li><strong className="text-zinc-200">Correction:</strong> Update inaccurate personal information in your profile</li>
              <li><strong className="text-zinc-200">Deletion:</strong> Request account and data deletion (via profile settings or feedback)</li>
              <li><strong className="text-zinc-200">Portability:</strong> Receive your data in a machine-readable format</li>
              <li><strong className="text-zinc-200">Opt-out:</strong> Unsubscribe from non-essential communications</li>
            </ul>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">9. Cookies</h2>
            <p>We use HTTP-only session cookies for authentication. We also use browser localStorage for preferences (e.g., tutorial state, chat history). We do not use advertising or tracking cookies.</p>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">10. Data Retention</h2>
            <p>We retain your data as long as your account is active. Upon account deletion, data is removed within 30 days. Anonymised aggregate data (not linked to your identity) may be retained indefinitely for platform improvement.</p>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">11. Changes to this Policy</h2>
            <p>We may update this Privacy Policy from time to time. We will notify you of significant changes via email or in-app notification. Continued use of the Platform after changes constitutes acceptance.</p>
          </section>

          <section>
            <h2 className="text-white text-lg font-heading font-bold mb-3">12. Contact Us</h2>
            <p>For privacy concerns, data requests, or to report a violation, please use the feedback button in the app. We aim to respond within 7 business days.</p>
          </section>

        </div>

        <div className="mt-12 pt-8 border-t border-white/10 flex gap-4 text-xs text-zinc-600 font-body">
          <a href="/terms" className="hover:text-zinc-400">Terms &amp; Conditions</a>
          <span>·</span>
          <a href="/" className="hover:text-zinc-400">Home</a>
        </div>
      </div>
    </div>
  );
}
