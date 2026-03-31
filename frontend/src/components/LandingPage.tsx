import React from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, Shield, Zap, Globe, BarChart3, 
  ArrowRight, CheckCircle2, ChevronRight, Calculator
} from 'lucide-react';
import { useBillStore } from '../store/useBillStore';
import { useAuthStore } from '../store/useAuthStore';

const LandingPage: React.FC = () => {
  const { setViewMode } = useBillStore();
  const { token } = useAuthStore();

  const services = [
    {
      title: "Bill Generator",
      titleHi: "बिल जनरेटर",
      desc: "Complete bill package with all documents and PDFs.",
      descHi: "सभी दस्तावेजों और पीडीएफ के साथ पूरा बिल पैकेज।",
      icon: <FileText className="text-gold-500" />,
      color: "from-primary-400/20 to-primary-600/20"
    },
    {
      title: "Excel to Unified",
      titleHi: "एक्सेल से यूनिफाइड",
      desc: "Convert complex Excel sheets to standardized PWD models.",
      descHi: "जटिल एक्सेल शीट को मानकीकृत पीडब्ल्यूडी मॉडल में बदलें।",
      icon: <Zap className="text-saffron-500" />,
      color: "from-saffron-400/20 to-orange-600/20"
    },
    {
      title: "AI Note Sheets",
      titleHi: "एआई नोट शीट",
      desc: "Auto-generate Hindi/English note sheets with logic.",
      descHi: "तर्क के साथ हिंदी/अंग्रेजी नोट शीट स्वतः उत्पन्न करें।",
      icon: <Calculator className="text-blue-400" />,
      color: "from-blue-400/20 to-indigo-600/20"
    },
    {
      title: "Secure Auth",
      titleHi: "सुरक्षित प्रमाणीकरण",
      desc: "Enterprise-grade JWT authentication and role-based access.",
      descHi: "एंटरप्राइज़-ग्रेड JWT प्रमाणीकरण और भूमिका-आधारित पहुँच।",
      icon: <Shield className="text-green-400" />,
      color: "from-green-400/20 to-emerald-600/20"
    },
    {
      title: "Live Preview",
      titleHi: "लाइव पूर्वावलोकन",
      desc: "See document changes in real-time as you edit items.",
      descHi: "आइटम संपादित करते समय रीयल-टाइम में दस्तावेज़ परिवर्तन देखें।",
      icon: <BarChart3 className="text-purple-400" />,
      color: "from-purple-400/20 to-violet-600/20"
    },
    {
      title: "Bilingual UI",
      titleHi: "द्विभाषी यूआई",
      desc: "Optimized for both Hindi and English users.",
      descHi: "हिंदी और अंग्रेजी दोनों उपयोगकर्ताओं के लिए अनुकूलित।",
      icon: <Globe className="text-indigo-400" />,
      color: "from-indigo-400/20 to-blue-600/20"
    }
  ];

  return (
    <div className="min-h-screen bg-surface-950 overflow-x-hidden selection:bg-gold-500/30">
      {/* Background Decorative Elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-primary-500/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-gold-500/5 rounded-full blur-[100px]" />
      </div>

      {/* Hero Section */}
      <section className="relative pt-24 pb-20 px-6 max-w-7xl mx-auto z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <motion.div 
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-gold-400 text-xs font-semibold uppercase tracking-wider mb-6">
              <Zap size={14} className="fill-gold-400" />
              <span>Next-Gen PWD Solution • २०२६</span>
            </div>
            
            <h1 className="text-5xl lg:text-7xl font-heading font-extrabold text-white leading-[1.1] mb-6">
              Professional <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-400 via-saffron-400 to-gold-600">
                Bill Generator
              </span>
            </h1>
            
            <p className="text-lg text-slate-400 mb-8 max-w-xl leading-relaxed">
              Generate standardized PWD contractor bills, note sheets, and certificates in seconds. 
              <span className="hindi block mt-2 font-medium text-slate-300">
                पीडब्ल्यूडी ठेकेदार बिल, नोट शीट और प्रमाण पत्र तेजी से तैयार करें।
              </span>
            </p>

            <div className="flex flex-wrap gap-4">
              <button 
                onClick={() => setViewMode('dashboard')}
                className="btn-gold group"
              >
                Get Started Now <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
              </button>
              <button className="btn-primary">
                View Documentation
              </button>
            </div>

            <div className="mt-10 flex items-center gap-6">
              <div className="flex -space-x-3">
                {[1,2,3,4].map(i => (
                  <div key={i} className="w-10 h-10 rounded-full border-2 border-surface-950 bg-surface-800 flex items-center justify-center text-xs font-bold text-white overflow-hidden">
                    <img src={`https://i.pravatar.cc/100?u=${i}`} alt="user" />
                  </div>
                ))}
              </div>
              <div className="text-sm">
                <div className="flex items-center gap-1 text-gold-400">
                  {[1,2,3,4,5].map(i => <CheckCircle2 key={i} size={14} fill="currentColor" className="text-gold-500" />)}
                </div>
                <p className="text-slate-500 font-medium tracking-tight">Trusted by 500+ Contractors</p>
              </div>
            </div>
          </motion.div>

          {/* Hero Image Container */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="relative z-10 glass-card p-4 rounded-3xl overflow-hidden shadow-2xl group transition-all duration-500 hover:shadow-indigo-500/20">
              <img 
                src="C:\Users\Rajkumar.DESKTOP-4ISBKM0\.gemini\antigravity\brain\ff22cd05-d838-4ad6-b5da-19b7b38f44ea\bill_generator_hero_3d_1774925303584.png" 
                alt="Bill Generator 3D Visual"
                className="rounded-2xl transition-transform duration-700 group-hover:scale-[1.02]"
              />
              <div className="absolute inset-0 bg-gradient-to-tr from-primary-600/40 to-transparent pointer-events-none" />
            </div>
            
            {/* Floating Badges */}
            <motion.div 
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -top-6 -right-6 glass p-4 rounded-2xl shadow-xl z-20 hidden sm:block border-primary-400/30"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <CheckCircle2 size={24} className="text-green-400" />
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Accuracy</p>
                  <p className="text-lg font-heading font-bold text-white">100.0%</p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Services Section */}
      <section className="relative py-24 bg-surface-900/50 z-10 border-y border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl font-heading font-bold text-white mb-4">
              All-In-One PWD Toolkit
              <span className="hindi block mt-1 text-2xl text-gold-400">सभी पीडब्ल्यूडी डिजिटल टूल्स</span>
            </h2>
            <div className="w-20 h-1 bg-gold-500 mx-auto rounded-full" />
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((s, i) => (
              <motion.div 
                key={i}
                whileHover={{ y: -8 }}
                className={`glass-card p-8 group flex flex-col items-center text-center`}
              >
                <div className={`w-14 h-14 rounded-2xl bg-white/5 flex items-center justify-center mb-6 transition-all duration-300 group-hover:scale-110 group-hover:shadow-[0_0_20px_rgba(255,255,255,0.1)]`}>
                  {s.icon}
                </div>
                <h3 className="text-xl font-heading font-bold text-white mb-1">{s.title}</h3>
                <h4 className="hindi text-gold-500 font-medium mb-3">{s.titleHi}</h4>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">{s.desc}</p>
                <p className="hindi text-xs text-slate-500 leading-relaxed">{s.descHi}</p>
                
                <div className="mt-auto pt-6 w-full flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronRight size={18} className="text-gold-500" />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer / CTA Section */}
      <section className="py-24 px-6 z-10">
        <div className="max-w-4xl mx-auto glass-card p-12 text-center rounded-[40px] relative overflow-hidden overflow-hidden overflow-hidden overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary-500/20 blur-[100px] pointer-events-none" />
          
          <h2 className="text-4xl lg:text-5xl font-heading font-extrabold text-white mb-6">
            Ready to generate your first bill?
          </h2>
          <p className="text-slate-400 mb-10 text-lg">
            Join hundreds of contractors saving hours every day on paperwork.
          </p>
          <button 
            onClick={() => setViewMode('dashboard')}
            className="btn-gold px-12 py-4 text-lg"
          >
            Go to My Dashboard
          </button>
        </div>
      </section>

      {/* Credits */}
      <footer className="py-12 border-t border-white/5 text-center text-slate-600 text-sm">
        <p>© 2026 BillForge • Made with ❤️ for PWD Rajasthan • Udaipur, Rajasthan</p>
      </footer>
    </div>
  );
};

export default LandingPage;
