import { Link } from 'react-router-dom';
import {
  Shield, UserCog, Building2, FileSearch, ScanSearch, Scale, ArrowRight, FilePlus, Search,
} from 'lucide-react';

/**
 * Landing page for Pramaan.
 * Two entry points: AICTE officers (login -> dashboard) and colleges (application portal).
 */

const FEATURES = [
  { icon: FileSearch, title: 'Validate', text: 'Completeness and consistency checks across the whole application.' },
  { icon: ScanSearch, title: 'Authenticate', text: 'Tamper detection and cross-document verification.' },
  { icon: Scale, title: 'Comply', text: 'Rule-by-rule checks against AICTE norms, with clause references.' },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-primary-900 text-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center">
          <div className="flex items-center gap-3">
            <div className="bg-primary-600 p-2 rounded-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold leading-tight tracking-tight">
                Pramaan <span className="font-normal text-primary-300">| प्रमाण</span>
              </h1>
              <p className="text-xs text-primary-300 leading-none">AI-Powered Application Verification</p>
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-b from-primary-900 to-primary-800 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-14 text-center">
          <p className="text-primary-300 text-sm font-medium tracking-wide uppercase mb-3">
            Smart Automation for AICTE Approvals
          </p>
          <h2 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">Proof behind every approval.</h2>
          <p className="text-primary-200 text-lg max-w-2xl mx-auto">
            Pramaan validates applications, authenticates supporting documents and verifies regulatory
            compliance, so officers can decide faster and with confidence.
          </p>
        </div>
      </section>

      {/* Entry cards */}
      <section className="max-w-4xl w-full mx-auto px-4 sm:px-6 -mt-8">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Officer */}
          <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 flex flex-col">
            <div className="w-12 h-12 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center mb-4">
              <UserCog size={24} />
            </div>
            <h3 className="text-xl font-semibold text-gray-900">AICTE Officer</h3>
            <p className="text-sm text-gray-500 mt-1 mb-6 flex-1">
              Log in to review the application queue, inspect document evidence and take decisions.
            </p>
            <Link
              to="/officer-login"
              className="inline-flex items-center justify-center gap-2 bg-primary-700 text-white px-5 py-3 rounded-lg font-semibold hover:bg-primary-800 transition-colors"
            >
              Officer Login <ArrowRight size={16} />
            </Link>
          </div>

          {/* College */}
          <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 flex flex-col">
            <div className="w-12 h-12 rounded-lg bg-success-100 text-success-700 flex items-center justify-center mb-4">
              <Building2 size={24} />
            </div>
            <h3 className="text-xl font-semibold text-gray-900">College / Institution</h3>
            <p className="text-sm text-gray-500 mt-1 mb-6 flex-1">
              Apply for approval, upload your documents and track the status of your application.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/apply"
                className="flex-1 inline-flex items-center justify-center gap-2 bg-success-600 text-white px-5 py-3 rounded-lg font-semibold hover:bg-success-700 transition-colors"
              >
                <FilePlus size={16} /> New Application
              </Link>
              <Link
                to="/track"
                className="flex-1 inline-flex items-center justify-center gap-2 bg-white text-gray-700 border border-gray-300 px-5 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                <Search size={16} /> Track Status
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-4xl w-full mx-auto px-4 sm:px-6 py-12">
        <div className="grid sm:grid-cols-3 gap-6">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="text-center">
              <div className="w-10 h-10 mx-auto rounded-full bg-primary-100 text-primary-700 flex items-center justify-center mb-3">
                <Icon size={20} />
              </div>
              <h4 className="font-semibold text-gray-900">{title}</h4>
              <p className="text-sm text-gray-500 mt-1">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-gray-200 py-5 text-center text-xs text-gray-400">
        Pramaan · Prototype for Smart India Hackathon 2026 · Problem Statement SIH26261 (AICTE)
      </footer>
    </div>
  );
}
