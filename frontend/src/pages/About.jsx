import { APP_NAME, APP_TAGLINE } from "../utils/constants";

export default function About() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="minimal-container py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="minimal-heading minimal-heading-xl mb-6 text-5xl font-bold">
            About <span className="text-blue-600">{APP_NAME}</span>
          </h1>

          <p className="minimal-text text-xl mb-12 text-gray-600 max-w-3xl mx-auto leading-relaxed">
            {APP_TAGLINE}  
            <br />
            <br />
            <strong>{APP_NAME}</strong> is a futuristic AI-powered personal assistant
            designed exclusively for <strong>MSME leaders</strong>.  
            It connects with your email, Google Calendar, and WhatsApp to automate repetitive work,
            organize meetings, track follow-ups, and let you focus on strategy — not operations.
          </p>

          <div className="minimal-card p-8 md:p-12 max-w-4xl mx-auto text-left">
            <h2 className="minimal-heading minimal-heading-lg mb-6 text-blue-600">Our Vision</h2>
            <p className="minimal-text text-lg leading-relaxed mb-8">
              To empower business owners with intelligent tools that automate the mundane, 
              enhance decision-making, and free up valuable time for growth and creativity.
            </p>

            <h2 className="minimal-heading minimal-heading-lg mb-6 text-blue-600">Our Mission</h2>
            <p className="minimal-text text-lg leading-relaxed">
              ProjectAria.PA aims to bring enterprise-grade automation and analytics 
              to the MSME sector — packaged into a friendly, reliable, and always-available AI assistant.
            </p>
          </div>

          <div className="mt-12 minimal-text-tertiary">
            <p>Built with ❤️ in India for the next generation of entrepreneurs.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
