import { useState } from 'react';
import { Sparkles, Loader2, X, Code, CheckCircle } from 'lucide-react';
import { api } from '../lib/api';

interface Props {
  onClose: () => void;
  toast: (type: 'success' | 'error' | 'warning', msg: string) => void;
}

export default function TemplateGenerator({ onClose, toast }: Props) {
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [schema, setSchema] = useState<any>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast('error', 'Please describe the layout you want to generate.');
      return;
    }
    
    setGenerating(true);
    setSchema(null);
    try {
      const res = await api.generateTemplate(prompt);
      setSchema(res);
      toast('success', 'AI Template Schema generated successfully!');
    } catch (err) {
      toast('error', err instanceof Error ? err.message : 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleApply = () => {
    // In a real implementation this might map to BillEditor config or send to API
    toast('success', `Applied template config: ${schema?.name}`);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="glass-lg rounded-2xl w-full max-w-2xl animate-slide-up my-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <Sparkles size={20} className="text-yellow-400" />
            <h2 className="font-semibold text-white">AI Template Generator</h2>
          </div>
          <button onClick={onClose} className="btn-ghost p-1.5"><X size={18} /></button>
        </div>

        <div className="p-5 space-y-4">
          {/* Prompt Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Describe your Bill Format</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. PWD Rajasthan Running Bill format with 5 columns for Item No, Description, Qty, Rate, Total..."
              className="w-full h-24 bg-white/[0.03] border border-white/[0.1] rounded-xl p-3 text-sm text-white focus:outline-none focus:border-yellow-500/50 resize-none"
              disabled={generating}
            />
          </div>

          {!schema ? (
            <div className="flex justify-center py-4">
              <button 
                onClick={handleGenerate}
                disabled={generating || !prompt.trim()}
                className="btn-primary flex items-center gap-2 bg-yellow-600 hover:bg-yellow-500 text-black font-semibold shadow-yellow-500/20 px-6 py-3 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generating ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Generating Template Schema...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Generate layout via AI
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-4 animate-slide-up">
              <div className="flex items-center gap-2 mb-2">
                <Code size={16} className="text-slate-400" />
                <h3 className="text-sm font-medium text-slate-300">Generated JSON Schema</h3>
              </div>
              
              <div className="bg-black/50 border border-white/[0.1] rounded-xl p-4 overflow-x-auto max-h-64 overflow-y-auto">
                <pre className="text-xs text-yellow-100/80 font-mono">
                  {JSON.stringify(schema, null, 2)}
                </pre>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4">
                <button 
                  onClick={() => setSchema(null)} 
                  className="btn-ghost"
                >
                  Edit Prompt & Regenerate
                </button>
                <button 
                  onClick={handleApply} 
                  className="btn-primary flex items-center justify-center gap-1.5 bg-yellow-600 hover:bg-yellow-500 text-black font-semibold"
                >
                  <CheckCircle size={15} /> Apply Schema
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
