import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Send, FileText, Sparkles } from 'lucide-react';
import { useAIAsk, usePolicyBrief, useCorridors } from '@/api/hooks';
import { SectionTitle, LoadingBlock, AlertBanner, EmptyState } from '@/components/ui';

const SUGGESTED = [
  'What are the most urgent wildlife corridor interventions needed in Karnataka right now?',
  'If a new 4-lane highway is built through the Bannerghatta corridor, what will happen to elephant migration?',
  'Rank the 3 Karnataka corridors by conservation ROI and explain the reasoning.',
  'What satellite data layers are most important for wildlife corridor prediction and why?',
  'Explain how a Graph Neural Network models wildlife movement between habitat patches.',
];

interface ChatMsg { role: 'user' | 'ai'; text: string; }

export default function AIInsightsPage() {
  const [input, setInput]   = useState('');
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [briefCorridor, setBriefCorridor] = useState<number | undefined>(undefined);
  const bottomRef = useRef<HTMLDivElement>(null);

  const ask    = useAIAsk();
  const brief  = usePolicyBrief();
  const { data: corridors } = useCorridors();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, ask.isPending]);

  const submit = async (q?: string) => {
    const question = (q ?? input).trim();
    if (!question) return;
    setMessages(m => [...m, { role: 'user', text: question }]);
    setInput('');
    try {
      const res = await ask.mutateAsync({ question });
      setMessages(m => [...m, { role: 'ai', text: res.answer }]);
    } catch {
      setMessages(m => [...m, { role: 'ai', text: 'AI service unavailable. Please check ANTHROPIC_API_KEY configuration on the backend.' }]);
    }
  };

  const generateBrief = async () => {
    await brief.mutateAsync({ corridorId: briefCorridor, audience: 'Karnataka Forest Department' });
  };

  return (
    <div className="p-5 h-full flex flex-col gap-5">
      <div className="flex-shrink-0">
        <h1 className="text-xl font-semibold text-[#e8f5e9]">AI Conservation Intelligence</h1>
        <p className="text-sm text-[#5a7a5a] mt-0.5">Ask Claude anything about Karnataka's wildlife corridors, infrastructure impacts, or restoration strategy</p>
      </div>

      <div className="grid grid-cols-3 gap-5 flex-1 min-h-0">
        {/* Chat */}
        <div className="col-span-2 card flex flex-col min-h-0">
          <SectionTitle><Brain size={12} className="inline mr-1" />Ask Anything</SectionTitle>

          {messages.length === 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {SUGGESTED.map(q => (
                <button key={q} onClick={() => submit(q)}
                  className="text-xs px-3 py-1.5 rounded-full border border-[rgba(74,222,128,0.2)] text-forest-400 hover:bg-[rgba(74,222,128,0.06)] transition-colors">
                  {q.length > 50 ? q.slice(0, 50) + '…' : q} ↗
                </button>
              ))}
            </div>
          )}

          <div className="flex-1 overflow-y-auto space-y-3 mb-3 min-h-[200px]">
            {messages.length === 0 && !ask.isPending && (
              <EmptyState message="Ask a question or pick a suggestion above to get started" />
            )}
            <AnimatePresence>
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-forest-700 text-white'
                      : 'bg-[rgba(34,197,94,0.06)] border border-[rgba(34,197,94,0.15)] text-[#c8e6c9]'
                  }`}>
                    {m.role === 'ai' && (
                      <div className="flex items-center gap-1 text-xs text-forest-400 mb-1 font-medium">
                        <Sparkles size={10} /> ConnectAI
                      </div>
                    )}
                    {m.text}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {ask.isPending && (
              <div className="flex justify-start">
                <div className="bg-[rgba(34,197,94,0.06)] border border-[rgba(34,197,94,0.15)] rounded-lg px-3 py-2 text-sm flex items-center gap-2 text-[#8aab8a]">
                  <span className="spinner" /> Analysing…
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="flex gap-2 flex-shrink-0">
            <input
              className="input-field flex-1"
              placeholder="Ask about Karnataka corridors, species, infrastructure impacts…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && submit()}
            />
            <button onClick={() => submit()} disabled={ask.isPending} className="btn-primary !px-3">
              <Send size={14} />
            </button>
          </div>
        </div>

        {/* Policy Brief Generator */}
        <div className="card flex flex-col">
          <SectionTitle><FileText size={12} className="inline mr-1" />Policy Brief Generator</SectionTitle>
          <p className="text-xs text-[#5a7a5a] mb-3">Generate a formal government policy brief for Karnataka Forest Department officers.</p>

          <label className="text-xs text-[#5a7a5a] mb-1.5 block">Scope</label>
          <select className="select-field mb-3" value={briefCorridor ?? ''} onChange={e => setBriefCorridor(e.target.value ? +e.target.value : undefined)}>
            <option value="">All Corridors (Summary)</option>
            {(corridors ?? []).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>

          <button onClick={generateBrief} disabled={brief.isPending} className="btn-outline w-full justify-center mb-4">
            {brief.isPending ? <><span className="spinner" />Generating…</> : <><FileText size={14} />Generate Brief</>}
          </button>

          <div className="flex-1 overflow-y-auto">
            {brief.isPending && <LoadingBlock label="Drafting policy brief…" />}
            {brief.data && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
                <div className="text-xs text-[#5a7a5a] flex justify-between">
                  <span>{brief.data.audience}</span>
                  <span className="text-amber-400">{brief.data.classification}</span>
                </div>
                <div className="bg-[rgba(34,197,94,0.04)] border border-[rgba(34,197,94,0.12)] rounded-lg p-3 text-sm text-[#c8e6c9] leading-relaxed whitespace-pre-line">
                  {brief.data.policy_brief}
                </div>
              </motion.div>
            )}
            {!brief.isPending && !brief.data && <EmptyState message="Generated brief will appear here" />}
          </div>

          {brief.isError && <AlertBanner variant="error" className="mt-2">Failed to generate brief</AlertBanner>}
        </div>
      </div>
    </div>
  );
}
