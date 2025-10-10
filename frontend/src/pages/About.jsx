import { APP_NAME, APP_TAGLINE } from "../utils/constants";

export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 flex flex-col items-center pt-24 px-6 text-center">
      <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4">
        About <span className="text-blue-600">{APP_NAME}</span>
      </h1>

      <p className="text-gray-600 max-w-2xl text-lg leading-relaxed mb-8">
        {APP_TAGLINE}  
        <br />
        <br />
        <strong>{APP_NAME}</strong> is a futuristic AI-powered personal assistant
        designed exclusively for <strong>MSME leaders</strong>.  
        It connects with your email, Google Calendar, and WhatsApp to automate repetitive work,
        organize meetings, track follow-ups, and let you focus on strategy — not operations.
      </p>

      <div className="max-w-3xl mt-8 text-left bg-white shadow-md rounded-2xl p-6 md:p-10 border border-gray-100">
        <h2 className="text-2xl font-semibold text-blue-600 mb-3">Our Vision</h2>
        <p className="text-gray-700 leading-relaxed">
          To empower business owners with intelligent tools that automate the mundane, 
          enhance decision-making, and free up valuable time for growth and creativity.
        </p>

        <h2 className="text-2xl font-semibold text-blue-600 mt-8 mb-3">Our Mission</h2>
        <p className="text-gray-700 leading-relaxed">
          ProjectAria.PA aims to bring enterprise-grade automation and analytics 
          to the MSME sector — packaged into a friendly, reliable, and always-available AI assistant.
        </p>
      </div>

      <div className="mt-12 text-gray-500 text-sm">
        <p>Built with ❤️ in India for the next generation of entrepreneurs.</p>
      </div>
    </div>
  );
}
