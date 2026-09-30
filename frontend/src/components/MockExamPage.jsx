import {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from 'react';

import {
  motion,
  AnimatePresence,
} from 'framer-motion';

import {
  FileText,
  Clock,
  Sparkles,
  ChevronDown,
  CheckCircle,
  AlertCircle,
  Zap,
  RotateCcw,
  BookOpen,
  Target,
  RefreshCw,
} from 'lucide-react';

import axios from 'axios';

import { useAuth } from '../contexts/AuthContext';
import { MathText } from './MathRenderer';


const API =
  `${process.env.REACT_APP_BACKEND_URL}/api`;


const PENDING_JOB_KEY =
  'aceit_pending_mock_exam_job';


const POLL_INTERVAL =
  2000;


function Timer({
  durationMinutes,
  initialSeconds,
  onTimeUp,
  running,
}) {
  const [seconds, setSeconds] =
    useState(
      initialSeconds !== undefined
        ? initialSeconds
        : durationMinutes * 60
    );

  const intervalRef =
    useRef(null);


  useEffect(() => {
    if (!running) {
      return;
    }

    intervalRef.current =
      setInterval(() => {
        setSeconds((current) => {
          if (current <= 1) {
            clearInterval(
              intervalRef.current
            );

            onTimeUp();

            return 0;
          }

          return current - 1;
        });
      }, 1000);


    return () =>
      clearInterval(
        intervalRef.current
      );
  }, [
    running,
    onTimeUp,
  ]);


  const mins =
    Math.floor(seconds / 60);

  const secs =
    seconds % 60;


  const urgent =
    seconds < 300;


  return (
    <div
      className={`flex items-center gap-2 px-3 py-2 rounded-xl border ${
        urgent
          ? 'border-red-500/30 bg-red-500/10'
          : 'border-white/10 bg-zinc-900/50'
      }`}
    >
      <Clock
        size={14}
        className={
          urgent
            ? 'text-red-400 animate-pulse'
            : 'text-zinc-400'
        }
      />

      <span
        className={`font-heading font-bold text-sm ${
          urgent
            ? 'text-red-400'
            : 'text-white'
        }`}
      >
        {String(mins).padStart(2, '0')}:
        {String(secs).padStart(2, '0')}
      </span>
    </div>
  );
}


export default function MockExamPage() {
  const { user } =
    useAuth();


  const userClass =
    user?.class_level || '9';


  const isNios =
    user?.school === 'nios';


  const isBnps =
    user?.school ===
    'brooklyn_national';


  const savedExamState =
    (() => {
      try {
        const saved =
          JSON.parse(
            localStorage.getItem(
              'aceit_exam_state'
            ) || 'null'
          );

        if (
          !saved ||
          saved.phase !== 'exam'
        ) {
          return null;
        }

        const elapsed =
          Math.floor(
            (
              Date.now() -
              (
                saved.savedAt ||
                0
              )
            ) / 1000
          );

        const remainingSeconds =
          Math.max(
            0,
            (
              saved.examDurationSeconds ||
              0
            ) - elapsed
          );

        return {
          ...saved,
          remainingSeconds,
        };
      } catch {
        return null;
      }
    })();


  const [
    subjects,
    setSubjects,
  ] = useState([]);


  const [
    chapters,
    setChapters,
  ] = useState([]);


  const [
    form,
    setForm,
  ] = useState({
    class: userClass,
    subject: '',
    selectedChapters: [],
    duration: 60,
    numQ: 15,
  });


  const [
    exam,
    setExam,
  ] = useState(
    () =>
      savedExamState?.exam ||
      null
  );


  const [
    answers,
    setAnswers,
  ] = useState(
    () =>
      savedExamState?.answers ||
      {}
  );


  const [
    result,
    setResult,
  ] = useState(null);


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    phase,
    setPhase,
  ] = useState(
    () =>
      savedExamState
        ? 'exam'
        : 'setup'
  );


  const [
    currentSection,
    setCurrentSection,
  ] = useState(
    () =>
      savedExamState?.currentSection ||
      0
  );


  const [
    timerRunning,
    setTimerRunning,
  ] = useState(
    () => Boolean(savedExamState)
  );


  const [
    history,
    setHistory,
  ] = useState([]);


  const completedExams =
    useMemo(
      () =>
        history.filter(
          (item) =>
            item.completed
        ),
      [history]
    );


  const [
    weakAreas,
    setWeakAreas,
  ] = useState(null);


  const [
    followUp,
    setFollowUp,
  ] = useState(null);


  const [
    followUpLoading,
    setFollowUpLoading,
  ] = useState(false);


  const [
    generationJob,
    setGenerationJob,
  ] = useState(null);


  const [
    generationElapsed,
    setGenerationElapsed,
  ] = useState(0);


  const restoredTimerRef =
    useRef(
      savedExamState?.remainingSeconds
    );


  const pollTimeoutRef =
    useRef(null);


  const mountedRef =
    useRef(true);


  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;

      if (pollTimeoutRef.current) {
        clearTimeout(
          pollTimeoutRef.current
        );
      }
    };
  }, []);


  /*
   * Save an active exam locally.
   */
  useEffect(() => {
    if (
      phase === 'exam' &&
      exam
    ) {
      localStorage.setItem(
        'aceit_exam_state',
        JSON.stringify({
          phase,
          exam,
          answers,
          currentSection,
          savedAt:
            Date.now(),
          examDurationSeconds:
            exam.duration_minutes *
            60,
        })
      );
    }
  }, [
    phase,
    exam,
    answers,
    currentSection,
  ]);


  /*
   * Show elapsed generation time.
   */
  useEffect(() => {
    if (!generationJob) {
      setGenerationElapsed(0);
      return;
    }


    const started =
      generationJob.started_at
        ? new Date(
            generationJob.started_at
          ).getTime()
        : Date.now();


    const updateElapsed =
      () => {
        setGenerationElapsed(
          Math.max(
            0,
            Math.floor(
              (
                Date.now() -
                started
              ) / 1000
            )
          )
        );
      };


    updateElapsed();


    const timer =
      setInterval(
        updateElapsed,
        1000
      );


    return () =>
      clearInterval(timer);
  }, [
    generationJob,
  ]);


  /*
   * Poll the persistent mock-exam job.
   */
  const pollGenerationJob =
    useCallback(
      async (
        examId
      ) => {
        if (!examId) {
          return;
        }


        try {
          const response =
            await axios.get(
              `${API}/mock-exam/jobs/${examId}`,
              {
                withCredentials:
                  true,
              }
            );


          const job =
            response.data?.job;


          if (!job) {
            localStorage.removeItem(
              PENDING_JOB_KEY
            );

            setGenerationJob(
              null
            );

            return;
          }


          if (
            job.generation_status ===
            'generating'
          ) {
            setGenerationJob(
              job
            );


            localStorage.setItem(
              PENDING_JOB_KEY,
              examId
            );


            if (
              mountedRef.current
            ) {
              pollTimeoutRef.current =
                setTimeout(
                  () =>
                    pollGenerationJob(
                      examId
                    ),
                  POLL_INTERVAL
                );
            }


            return;
          }


          if (
            job.generation_status ===
              'ready' &&
            job.sections?.length
          ) {
            localStorage.removeItem(
              PENDING_JOB_KEY
            );


            setGenerationJob(
              null
            );


            setExam(job);

            setAnswers({});

            setCurrentSection(
              0
            );

            restoredTimerRef.current =
              undefined;

            setPhase(
              'exam'
            );

            setTimerRunning(
              true
            );


            setHistory(
              (previous) => [
                job,
                ...previous.filter(
                  (item) =>
                    item.exam_id !==
                    job.exam_id
                ),
              ]
            );


            return;
          }


          if (
            job.generation_status ===
            'error'
          ) {
            localStorage.removeItem(
              PENDING_JOB_KEY
            );


            setGenerationJob(
              null
            );


            window.alert(
              job.generation_message ||
                'Mock exam generation failed.'
            );


            return;
          }


        } catch {
          /*
           * Keep trying.
           *
           * A temporary network problem must
           * not delete the generation job.
           */
          if (
            mountedRef.current
          ) {
            pollTimeoutRef.current =
              setTimeout(
                () =>
                  pollGenerationJob(
                    examId
                  ),
                POLL_INTERVAL * 2
              );
          }
        }
      },
      []
    );


  /*
   * Load page data + reconnect to server-side
   * generation after a reload/navigation.
   */
  useEffect(() => {
    let cancelled = false;


    const load =
      async () => {

        setForm(
          (previous) => ({
            ...previous,
            class:
              userClass,
          })
        );


        const responses =
          await Promise.allSettled([
            axios.get(
              `${API}/syllabus/${userClass}/subjects`,
              {
                withCredentials:
                  true,
              }
            ),

            axios.get(
              `${API}/mock-exam/history`,
              {
                withCredentials:
                  true,
              }
            ),

            axios.get(
              `${API}/weak-areas`,
              {
                withCredentials:
                  true,
              }
            ),

            axios.get(
              `${API}/mock-exam/jobs/active`,
              {
                withCredentials:
                  true,
              }
            ),
          ]);


        if (cancelled) {
          return;
        }


        const [
          subjectsResponse,
          historyResponse,
          weakResponse,
          activeJobResponse,
        ] = responses;


        if (
          subjectsResponse.status ===
          'fulfilled'
        ) {
          setSubjects(
            subjectsResponse.value
              .data || []
          );
        }


        if (
          historyResponse.status ===
          'fulfilled'
        ) {
          setHistory(
            historyResponse.value
              .data || []
          );
        }


        if (
          weakResponse.status ===
          'fulfilled'
        ) {
          setWeakAreas(
            weakResponse.value
              .data
          );
        }


        const savedJob =
          localStorage.getItem(
            PENDING_JOB_KEY
          );


        if (savedJob) {
          await pollGenerationJob(
            savedJob
          );

        } else if (
          activeJobResponse.status ===
            'fulfilled' &&
          activeJobResponse.value
            .data?.job?.exam_id
        ) {
          const job =
            activeJobResponse.value
              .data.job;


          setGenerationJob(
            job
          );


          localStorage.setItem(
            PENDING_JOB_KEY,
            job.exam_id
          );


          await pollGenerationJob(
            job.exam_id
          );
        }
      };


    load();


    return () => {
      cancelled = true;
    };


    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    userClass,
  ]);


  const onSubjectChange =
    async (
      subject
    ) => {

      setForm(
        (previous) => ({
          ...previous,
          subject,
          selectedChapters: [],
        })
      );


      if (!subject) {
        setChapters([]);
        return;
      }


      try {
        const response =
          await axios.get(
            `${API}/syllabus/${form.class}/${encodeURIComponent(subject)}/chapters`,
            {
              withCredentials:
                true,
            }
          );


        setChapters(
          Array.isArray(
            response.data
          )
            ? response.data
            : (
                response.data
                  ?.chapters ||
                []
              )
        );

      } catch {
        setChapters([]);
      }
    };


  const toggleChapter =
    (
      chapterName
    ) => {
      setForm(
        (previous) => {

          const selected =
            previous.selectedChapters;


          if (
            selected.includes(
              chapterName
            )
          ) {
            return {
              ...previous,
              selectedChapters:
                selected.filter(
                  (chapter) =>
                    chapter !==
                    chapterName
                ),
            };
          }


          if (
            selected.length >=
            7
          ) {
            return previous;
          }


          return {
            ...previous,
            selectedChapters: [
              ...selected,
              chapterName,
            ],
          };
        }
      );
    };


  const generateExam =
    async () => {

      if (
        !form.class ||
        !form.subject ||
        generationJob
      ) {
        return;
      }


      setLoading(true);


      try {
        const response =
          await axios.post(
            `${API}/mock-exam/generate`,
            {
              class_level:
                form.class,

              subject:
                form.subject,

              chapters:
                form.selectedChapters,

              duration_minutes:
                form.duration,

              num_questions:
                form.numQ,
            },
            {
              withCredentials:
                true,
            }
          );


        const job = {
          ...response.data,

          generation_status:
            response.data.status ||
            'generating',

          started_at:
            response.data.started_at ||
            new Date().toISOString(),
        };


        setGenerationJob(
          job
        );


        localStorage.setItem(
          PENDING_JOB_KEY,
          response.data.exam_id
        );


        setLoading(false);


        pollGenerationJob(
          response.data.exam_id
        );

      } catch (error) {

        console.error(
          '[AceIt] Mock generation start error:',
          error
        );


        const message =
          error?.response?.data
            ?.detail?.message ||
          error?.response?.data
            ?.detail ||
          'Could not start mock exam generation.';


        window.alert(
          message
        );


        setLoading(false);
      }
    };


  const submitExam =
    async () => {

      if (!exam) {
        return;
      }


      setTimerRunning(
        false
      );

      setLoading(
        true
      );


      try {
        const response =
          await axios.post(
            `${API}/mock-exam/${exam.exam_id}/submit`,
            {
              quiz_id:
                exam.exam_id,
              answers,
            },
            {
              withCredentials:
                true,
            }
          );


        setResult(
          response.data
        );


        setPhase(
          'result'
        );


        localStorage.removeItem(
          'aceit_exam_state'
        );


        const historyResponse =
          await axios.get(
            `${API}/mock-exam/history`,
            {
              withCredentials:
                true,
            }
          );


        setHistory(
          historyResponse.data
            || []
        );

      } catch (error) {

        console.error(
          '[AceIt] Submit error:',
          error
        );


        window.alert(
          error?.response?.data
            ?.detail ||
            'Could not submit the exam.'
        );
      }


      setLoading(
        false
      );
    };


  const handleTimeUp =
    useCallback(
      () => {
        setTimerRunning(
          false
        );

        submitExam();
      },
      [
        exam,
        answers,
      ]
    );


  const reset = () => {

    localStorage.removeItem(
      'aceit_exam_state'
    );


    setPhase(
      'setup'
    );

    setExam(
      null
    );

    setResult(
      null
    );

    setAnswers(
      {}
    );

    setTimerRunning(
      false
    );

    setFollowUp(
      null
    );


    restoredTimerRef.current =
      undefined;
  };


  const startFollowUp =
    async () => {

      if (!exam) {
        return;
      }


      setFollowUpLoading(
        true
      );


      try {
        const response =
          await axios.post(
            `${API}/mock-exam/${exam.exam_id}/followup-quiz`,
            {},
            {
              withCredentials:
                true,
            }
          );


        setFollowUp({
          quiz:
            response.data,

          answers:
            {},

          submitted:
            null,
        });

      } catch (error) {

        console.error(
          '[AceIt] Follow-up error:',
          error
        );


        window.alert(
          error?.response?.data
            ?.detail ||
            'Could not generate practice quiz.'
        );
      }


      setFollowUpLoading(
        false
      );
    };


  const submitFollowUp =
    async () => {

      if (
        !followUp?.quiz
      ) {
        return;
      }


      setFollowUpLoading(
        true
      );


      try {
        const response =
          await axios.post(
            `${API}/quiz/${followUp.quiz.quiz_id}/submit`,
            {
              quiz_id:
                followUp.quiz.quiz_id,

              answers:
                followUp.answers,
            },
            {
              withCredentials:
                true,
            }
          );


        setFollowUp(
          (previous) => ({
            ...previous,
            submitted:
              response.data,
          })
        );

      } catch (error) {

        console.error(
          '[AceIt] Follow-up submit error:',
          error
        );


        window.alert(
          error?.response?.data
            ?.detail ||
            'Could not submit practice quiz.'
        );
      }


      setFollowUpLoading(
        false
      );
    };


  const allQuestions =
    exam?.sections?.flatMap(
      (section) =>
        section.questions
    ) || [];


  const answeredCount =
    Object.keys(
      answers
    ).length;


  const selectClass =
    'w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-3 text-white text-sm font-body focus:outline-none focus:border-cyan-500/50 appearance-none';


  const estimate =
    generationJob
      ?.estimated_seconds ||
    45;


  const generationPercent =
    Math.min(
      95,
      Math.max(
        5,
        Math.round(
          (
            generationElapsed /
            estimate
          ) *
          100
        )
      )
    );


  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto">

      <div className="mb-5">

        <h1 className="text-2xl sm:text-3xl font-heading font-black text-white flex items-center gap-3">
          <FileText
            size={28}
            className="text-cyan-400"
          />

          Mock Exam
        </h1>


        <p className="text-zinc-500 text-sm font-body mt-1">
          {isNios
            ? 'NIOS Secondary Course timed examinations'
            : isBnps
            ? 'BNPS Grade 8 timed examinations'
            : 'Timed school examinations'}
        </p>

      </div>


      <AnimatePresence mode="wait">

        {phase === 'setup' && (
          <motion.div
            key="setup"
            initial={{
              opacity: 0,
              y: 10,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            exit={{
              opacity: 0,
            }}
            className="grid lg:grid-cols-2 gap-5"
          >

            <div className="glass rounded-2xl p-5 border border-white/10 space-y-4">

              <h2 className="text-white font-heading font-bold">
                Configure Exam
              </h2>


              <div className="grid grid-cols-2 gap-3">

                <div
                  className="px-3 py-3 rounded-xl border border-amber-400/30 bg-amber-500/10 text-amber-300 text-sm font-body font-semibold flex items-center gap-2"
                >
                  <BookOpen
                    size={14}
                  />

                  {isNios
                    ? 'Secondary Course'
                    : `Class ${userClass}`}
                </div>


                <div className="relative">

                  <select
                    value={
                      form.subject
                    }
                    onChange={
                      (
                        event
                      ) =>
                        onSubjectChange(
                          event.target.value
                        )
                    }
                    className={
                      selectClass
                    }
                    disabled={
                      generationJob
                    }
                  >

                    <option value="">
                      Subject
                    </option>

                    {subjects.map(
                      (subject) => (
                        <option
                          key={
                            subject.name
                          }
                          value={
                            subject.name
                          }
                        >
                          {
                            subject.name
                          }
                        </option>
                      )
                    )}

                  </select>


                  <ChevronDown
                    size={14}
                    className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none"
                  />

                </div>

              </div>


              {form.subject &&
                chapters.length >
                  0 && (
                <div>

                  <p className="text-zinc-500 text-xs font-body mb-2">

                    Select chapters

                    <span className="text-zinc-600">
                      {' '}
                      (up to 7 — leave empty for full syllabus)
                    </span>

                    {form.selectedChapters.length >
                      0 && (
                      <button
                        onClick={() =>
                          setForm(
                            (
                              previous
                            ) => ({
                              ...previous,
                              selectedChapters:
                                [],
                            })
                          )
                        }
                        className="ml-2 text-cyan-500 hover:text-cyan-400"
                      >
                        clear all
                      </button>
                    )}

                  </p>


                  <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">

                    {chapters.map(
                      (
                        chapter
                      ) => {

                        const name =
                          chapter.name ||
                          chapter;

                        const selected =
                          form.selectedChapters.includes(
                            name
                          );

                        const disabled =
                          !selected &&
                          form.selectedChapters.length >=
                            7;


                        return (
                          <button
                            key={name}
                            onClick={() =>
                              !disabled &&
                              toggleChapter(
                                name
                              )
                            }
                            disabled={
                              disabled ||
                              Boolean(
                                generationJob
                              )
                            }
                            className={`px-3 py-1.5 rounded-full text-xs font-body font-medium border transition-all ${
                              selected
                                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50'
                                : disabled
                                ? 'opacity-30 text-zinc-600 border-zinc-700'
                                : 'text-zinc-400 border-zinc-700 hover:border-zinc-500 hover:text-zinc-300'
                            }`}
                          >
                            {name}
                          </button>
                        );
                      }
                    )}

                  </div>


                  {form.selectedChapters.length >
                    0 && (
                    <p className="text-cyan-400 text-xs font-body mt-2">
                      {
                        form.selectedChapters.length
                      }
                      /7 chapters selected
                    </p>
                  )}

                </div>
              )}


              <div className="grid grid-cols-2 gap-3">

                <div className="relative">

                  <select
                    value={
                      form.duration
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setForm(
                          (
                            previous
                          ) => ({
                            ...previous,
                            duration:
                              Number(
                                event.target.value
                              ),
                          })
                        )
                    }
                    className={
                      selectClass
                    }
                    disabled={
                      Boolean(
                        generationJob
                      )
                    }
                  >

                    {[30, 60, 90, 180].map(
                      (duration) => (
                        <option
                          key={
                            duration
                          }
                          value={
                            duration
                          }
                        >
                          {
                            duration
                          }{' '}
                          min
                        </option>
                      )
                    )}

                  </select>

                  <ChevronDown
                    size={14}
                    className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none"
                  />

                </div>


                <div className="relative">

                  <select
                    value={
                      form.numQ
                    }
                    onChange={
                      (
                        event
                      ) =>
                        setForm(
                          (
                            previous
                          ) => ({
                            ...previous,
                            numQ:
                              Number(
                                event.target.value
                              ),
                          })
                        )
                    }
                    className={
                      selectClass
                    }
                    disabled={
                      Boolean(
                        generationJob
                      )
                    }
                  >

                    {[10, 15, 20, 30].map(
                      (number) => (
                        <option
                          key={
                            number
                          }
                          value={
                            number
                          }
                        >
                          {
                            number
                          }{' '}
                          Questions
                        </option>
                      )
                    )}

                  </select>

                  <ChevronDown
                    size={14}
                    className="absolute right-3 top-3.5 text-zinc-500 pointer-events-none"
                  />

                </div>

              </div>


              <div className="p-3 rounded-xl bg-cyan-500/5 border border-cyan-500/15 text-xs font-body text-cyan-300 space-y-1">

                <p>
                  • Three sections generate in parallel for faster exams
                </p>

                <p>
                  • {isNios
                    ? 'Strictly NIOS Secondary curriculum'
                    : isBnps
                    ? 'Strictly BNPS Grade 8 curriculum'
                    : 'Strictly the selected curriculum'}
                </p>

                <p>
                  • You can switch features or reload while it generates
                </p>

              </div>


              {generationJob && (
                <div className="rounded-2xl border border-violet-500/30 bg-violet-500/10 p-4">

                  <div className="flex items-start gap-3">

                    <div className="w-9 h-9 rounded-xl bg-violet-500/15 flex items-center justify-center flex-shrink-0">

                      <RefreshCw
                        size={17}
                        className="text-violet-400 animate-spin"
                      />

                    </div>


                    <div className="flex-1">

                      <p className="text-white font-heading font-bold text-sm">
                        Generating your mock exam
                      </p>


                      <p className="text-violet-300 text-xs font-body mt-1">

                        Estimated time:
                        {' '}
                        <strong>
                          ~{estimate} seconds
                        </strong>

                      </p>


                      <p className="text-zinc-500 text-xs font-body mt-1">
                        You can safely reload or switch to another feature. The generation continues on the server.
                      </p>


                      <div className="mt-3">

                        <div className="flex justify-between text-[11px] text-zinc-500 mb-1">

                          <span>
                            {generationElapsed}s elapsed
                          </span>

                          <span>
                            Usually ~{estimate}s
                          </span>

                        </div>


                        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">

                          <motion.div
                            className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500"
                            animate={{
                              width:
                                `${generationPercent}%`,
                            }}
                          />

                        </div>

                      </div>

                    </div>

                  </div>

                </div>
              )}


              <button
                onClick={
                  generateExam
                }
                disabled={
                  !form.class ||
                  !form.subject ||
                  loading ||
                  Boolean(
                    generationJob
                  )
                }
                className="w-full py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-black font-heading font-bold flex items-center justify-center gap-2"
              >

                {loading ||
                generationJob ? (
                  <>
                    <RefreshCw
                      size={16}
                      className="animate-spin"
                    />

                    {generationJob
                      ? 'Generating...'
                      : 'Starting...'}
                  </>
                ) : (
                  <>
                    <Sparkles
                      size={16}
                    />

                    Generate Mock Exam
                  </>
                )}

              </button>

            </div>


            {completedExams.length >
              0 && (
              <div>

                <h3 className="text-zinc-400 text-sm font-body font-semibold mb-3 uppercase tracking-wider">
                  Recent Scores
                </h3>


                <div className="space-y-2">

                  {completedExams.map(
                    (item) => (
                      <div
                        key={
                          item.exam_id
                        }
                        className="flex items-center gap-3 p-3 rounded-xl border border-white/5 bg-zinc-900/30"
                      >

                        <div
                          className="w-10 h-10 rounded-xl flex items-center justify-center font-heading font-black text-sm"
                          style={{
                            background:
                              item.score >=
                              70
                                ? '#10b98120'
                                : '#ef444420',

                            color:
                              item.score >=
                              70
                                ? '#10b981'
                                : '#ef4444',
                          }}
                        >
                          {
                            item.score
                          }%
                        </div>


                        <div className="flex-1 min-w-0">

                          <p className="text-white text-sm font-body font-medium truncate">
                            {
                              item.title
                            }
                          </p>

                          <p className="text-zinc-600 text-xs font-body">
                            {
                              new Date(
                                item.created_at
                              ).toLocaleDateString()
                            }
                          </p>

                        </div>

                      </div>
                    )
                  )}

                </div>

              </div>
            )}


            {weakAreas?.weak_topics?.length >
              0 && (
              <div>

                <h3 className="text-zinc-400 text-sm font-body font-semibold mb-3 uppercase tracking-wider flex items-center gap-2">

                  <Target
                    size={14}
                    className="text-red-400"
                  />

                  Weak Areas

                </h3>


                <div className="p-4 rounded-2xl border border-red-500/15 bg-red-500/5">

                  <div className="flex flex-wrap gap-2">

                    {weakAreas.weak_topics.slice(
                      0,
                      8
                    ).map(
                      ({
                        topic,
                        frequency,
                      }) => (
                        <span
                          key={
                            topic
                          }
                          className="px-3 py-1 rounded-full text-xs font-body border border-red-500/20 text-red-300 bg-red-500/5"
                        >
                          {topic}

                          {frequency >
                            1 && (
                            <span className="opacity-50 ml-1">
                              ×{frequency}
                            </span>
                          )}

                        </span>
                      )
                    )}

                  </div>

                </div>

              </div>
            )}

          </motion.div>
        )}


        {phase === 'exam' &&
          exam && (
          <motion.div
            key="exam"
            initial={{
              opacity: 0,
            }}
            animate={{
              opacity: 1,
            }}
          >

            <div className="flex items-center justify-between mb-4 p-3 glass rounded-xl border border-white/10">

              <div>

                <p className="text-white font-heading font-bold text-sm">
                  {
                    exam.title
                  }
                </p>

                <p className="text-zinc-500 text-xs font-body">
                  {answeredCount}/
                  {allQuestions.length}
                  {' '}
                  answered
                </p>

              </div>


              <div className="flex items-center gap-2">

                <Timer
                  key={
                    exam.exam_id
                  }
                  durationMinutes={
                    exam.duration_minutes
                  }
                  initialSeconds={
                    restoredTimerRef.current
                  }
                  onTimeUp={
                    handleTimeUp
                  }
                  running={
                    timerRunning
                  }
                />


                <button
                  onClick={
                    reset
                  }
                  className="p-1.5 rounded-lg text-zinc-600 hover:text-zinc-300"
                >
                  <RotateCcw
                    size={14}
                  />
                </button>

              </div>

            </div>


            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-4">

              <motion.div
                className="h-full bg-gradient-to-r from-cyan-400 to-violet-500"
                animate={{
                  width:
                    allQuestions.length
                      ? `${
                          (
                            answeredCount /
                            allQuestions.length
                          ) * 100
                        }%`
                      : '0%',
                }}
              />

            </div>


            <div className="flex gap-2 mb-4 overflow-x-auto">

              {exam.sections?.map(
                (
                  section,
                  index
                ) => (
                  <button
                    key={
                      section.section
                    }
                    onClick={() =>
                      setCurrentSection(
                        index
                      )
                    }
                    className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-body font-semibold ${
                      currentSection ===
                      index
                        ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                        : 'bg-zinc-900/50 text-zinc-500 border border-white/5'
                    }`}
                  >

                    Section
                    {' '}
                    {
                      section.section
                    }

                    <span className="ml-1 opacity-60 text-xs">
                      (
                      {
                        section
                          .questions
                          ?.length
                      }
                      Q)
                    </span>

                  </button>
                )
              )}

            </div>


            <div className="space-y-4">

              {exam.sections?.[
                currentSection
              ]?.questions?.map(
                (
                  question,
                  index
                ) => (
                  <motion.div
                    key={
                      question.id
                    }
                    initial={{
                      opacity: 0,
                      y: 5,
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                    }}
                    transition={{
                      delay:
                        index *
                        0.02,
                    }}
                    className={`glass-surface rounded-2xl p-4 border ${
                      answers[
                        question.id
                      ]
                        ? 'border-green-500/20'
                        : 'border-white/5'
                    }`}
                  >

                    <div className="flex items-start gap-3 mb-3">

                      <span className="px-2 py-0.5 rounded text-xs bg-cyan-500/10 text-cyan-400 font-heading font-bold">
                        {
                          question.id
                        }
                      </span>


                      <p className="text-white text-sm font-body leading-relaxed flex-1">
                        <MathText
                          text={
                            question.question
                          }
                        />
                      </p>


                      <span className="text-xs text-zinc-600">
                        [
                        {
                          question.marks
                        }m]
                      </span>

                    </div>


                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">

                      {question.options?.map(
                        (
                          option,
                          optionIndex
                        ) => {

                          const letter =
                            option.charAt(
                              0
                            );

                          const selected =
                            answers[
                              question.id
                            ] ===
                            letter;


                          return (
                            <button
                              key={
                                optionIndex
                              }
                              onClick={() =>
                                setAnswers(
                                  (
                                    previous
                                  ) => ({
                                    ...previous,
                                    [question.id]:
                                      letter,
                                  })
                                )
                              }
                              className={`text-left px-3 py-2.5 rounded-xl border flex items-center gap-2 ${
                                selected
                                  ? 'border-cyan-500/50 bg-cyan-500/10 text-white'
                                  : 'border-white/8 bg-zinc-900/30 text-zinc-300'
                              }`}
                            >

                              <span
                                className={`w-5 h-5 rounded-full border flex items-center justify-center text-xs ${
                                  selected
                                    ? 'border-cyan-400 text-cyan-400'
                                    : 'border-zinc-600 text-zinc-500'
                                }`}
                              >
                                {
                                  letter
                                }
                              </span>


                              <span>
                                {
                                  option.slice(
                                    3
                                  )
                                }
                              </span>

                            </button>
                          );
                        }
                      )}

                    </div>

                  </motion.div>
                )
              )}

            </div>


            <div className="mt-6 flex items-center justify-between">

              <p className="text-zinc-600 text-sm">
                {
                  allQuestions.length -
                  answeredCount
                }{' '}
                questions remaining
              </p>


              <button
                onClick={
                  submitExam
                }
                disabled={
                  loading
                }
                className="px-6 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-black font-heading font-bold flex items-center gap-2"
              >

                {loading ? (
                  <RefreshCw
                    size={15}
                    className="animate-spin"
                  />
                ) : (
                  <CheckCircle
                    size={16}
                  />
                )}

                Submit Exam

              </button>

            </div>

          </motion.div>
        )}


        {phase === 'result' &&
          result && (
          <motion.div
            key="result"
            initial={{
              opacity: 0,
              scale: 0.97,
            }}
            animate={{
              opacity: 1,
              scale: 1,
            }}
          >

            <div className="text-center py-8 glass rounded-2xl border border-white/10 mb-5">

              <div
                className="text-7xl font-heading font-black mb-2"
                style={{
                  color:
                    result.score >=
                    90
                      ? '#10b981'
                      : result.score >=
                        70
                      ? '#22d3ee'
                      : result.score >=
                        50
                      ? '#f59e0b'
                      : '#ef4444',
                }}
              >
                {
                  result.score
                }%
              </div>


              <p className="text-white font-heading font-bold text-xl">
                {result.score >=
                90
                  ? 'Outstanding Performance!'
                  : result.score >=
                    70
                  ? 'Well Done!'
                  : result.score >=
                    50
                  ? 'Good Effort!'
                  : 'Keep Practicing!'}
              </p>


              <p className="text-zinc-500 text-sm mt-1">
                {
                  result.earned_marks
                }/
                {
                  result.total_marks
                }{' '}
                marks
              </p>


              <div className="flex items-center justify-center gap-2 mt-3">

                <Zap
                  size={16}
                  className="text-amber-400"
                />

                <span className="text-amber-400 font-heading font-bold">
                  +{
                    result.xp_earned
                  }{' '}
                  XP
                </span>

              </div>

            </div>


            <div className="grid sm:grid-cols-3 gap-3 mb-5">

              {result.section_results?.map(
                (
                  section
                ) => (
                  <div
                    key={
                      section.section
                    }
                    className="glass-surface rounded-xl p-4 border border-white/5 text-center"
                  >

                    <p className="text-zinc-500 text-xs">
                      Section
                      {' '}
                      {
                        section.section
                      }
                    </p>

                    <p className="text-white text-xl font-heading font-black">
                      {
                        section.percentage
                      }%
                    </p>

                    <p className="text-zinc-600 text-xs">
                      {
                        section.marks_earned
                      }/
                      {
                        section.marks_total
                      }
                    </p>

                  </div>
                )
              )}

            </div>


            {result.weak_topics?.length >
              0 && (
              <div className="glass-surface rounded-xl p-4 border border-orange-500/15 mb-5">

                <div className="flex items-center gap-2 mb-3">

                  <AlertCircle
                    size={16}
                    className="text-orange-400"
                  />

                  <p className="text-white font-semibold text-sm">
                    Areas to Improve
                  </p>

                </div>


                <div className="flex flex-wrap gap-2 mb-3">

                  {result.weak_topics.map(
                    (
                      topic
                    ) => (
                      <span
                        key={
                          topic
                        }
                        className="px-2.5 py-1 rounded-full text-xs border border-orange-500/20 bg-orange-500/5 text-orange-300"
                      >
                        {
                          topic
                        }
                      </span>
                    )
                  )}

                </div>


                {!followUp && (
                  <button
                    onClick={
                      startFollowUp
                    }
                    disabled={
                      followUpLoading
                    }
                    className="w-full py-2.5 rounded-xl bg-orange-500/15 border border-orange-500/30 text-orange-300 font-heading font-bold flex items-center justify-center gap-2"
                  >

                    {followUpLoading ? (
                      <RefreshCw
                        size={15}
                        className="animate-spin"
                      />
                    ) : (
                      <Target
                        size={15}
                      />
                    )}

                    Practice Weak Areas (5 Qs)

                  </button>
                )}

              </div>
            )}


            {followUp?.quiz &&
              !followUp.submitted && (
              <div className="glass rounded-2xl p-5 border border-orange-500/20 mb-5 space-y-4">

                <p className="text-white font-heading font-bold">
                  {
                    followUp
                      .quiz
                      .title
                  }
                </p>


                {followUp.quiz.questions?.map(
                  (
                    question,
                    index
                  ) => (
                    <div
                      key={
                        index
                      }
                      className="p-3 rounded-xl bg-zinc-900/40 border border-white/5"
                    >

                      <p className="text-white text-sm mb-2">

                        <span className="text-orange-400 font-bold mr-2">
                          {index + 1}.
                        </span>

                        <MathText
                          text={
                            question.question
                          }
                        />

                      </p>


                      <div className="grid sm:grid-cols-2 gap-2">

                        {question.options?.map(
                          (
                            option,
                            optionIndex
                          ) => {

                            const letter =
                              option.charAt(
                                0
                              );

                            const selected =
                              followUp
                                .answers[
                                  String(
                                    index
                                  )
                                ] ===
                              letter;


                            return (
                              <button
                                key={
                                  optionIndex
                                }
                                onClick={() =>
                                  setFollowUp(
                                    (
                                      previous
                                    ) => ({
                                      ...previous,
                                      answers:
                                        {
                                          ...previous.answers,
                                          [String(
                                            index
                                          )]:
                                            letter,
                                        },
                                    })
                                  )
                                }
                                className={`text-left px-3 py-2 rounded-lg border ${
                                  selected
                                    ? 'border-orange-400/60 bg-orange-500/15 text-white'
                                    : 'border-white/8 bg-zinc-900/30 text-zinc-300'
                                }`}
                              >

                                <span className="mr-2">
                                  {
                                    letter
                                  }
                                </span>

                                {
                                  option.slice(
                                    3
                                  )
                                }

                              </button>
                            );
                          }
                        )}

                      </div>

                    </div>
                  )
                )}


                <button
                  onClick={
                    submitFollowUp
                  }
                  disabled={
                    followUpLoading ||
                    Object.keys(
                      followUp.answers
                    ).length ===
                      0
                  }
                  className="w-full py-2.5 rounded-xl bg-orange-500 text-black font-heading font-bold flex items-center justify-center gap-2"
                >

                  {followUpLoading ? (
                    <RefreshCw
                      size={15}
                      className="animate-spin"
                    />
                  ) : (
                    <CheckCircle
                      size={15}
                    />
                  )}

                  Submit Practice Quiz

                </button>

              </div>
            )}


            {followUp?.submitted && (
              <div className="glass rounded-2xl p-5 border border-orange-500/20 mb-5 text-center">

                <div className="text-5xl font-heading font-black text-orange-400">
                  {
                    followUp
                      .submitted
                      .score
                  }%
                </div>

                <p className="text-white font-heading font-bold mt-2">
                  Practice complete
                </p>

                <p className="text-zinc-500 text-sm mt-1">
                  {
                    followUp
                      .submitted
                      .correct_count
                  }/
                  {
                    followUp
                      .submitted
                      .total_questions
                  }{' '}
                  correct
                </p>

              </div>
            )}


            <button
              onClick={
                reset
              }
              className="w-full py-3 rounded-xl glass border border-white/10 text-white font-heading font-bold flex items-center justify-center gap-2"
            >

              <RotateCcw
                size={16}
              />

              Take Another Exam

            </button>

          </motion.div>
        )}

      </AnimatePresence>

    </div>
  );
}