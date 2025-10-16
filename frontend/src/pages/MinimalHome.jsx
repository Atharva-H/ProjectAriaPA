import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { 
  Calendar, 
  Mail, 
  MessageSquare, 
  Users, 
  Zap, 
  ArrowRight,
  CheckCircle2,
  Clock,
  Shield
} from "lucide-react";

export default function MinimalHome() {
  const { user } = useAuth();

  const features = [
    {
      icon: Calendar,
      title: "Smart Calendar",
      description: "AI-powered calendar management with intelligent scheduling and conflict resolution"
    },
    {
      icon: Mail,
      title: "Email Intelligence",
      description: "Extract tasks and insights from your emails automatically"
    },
    {
      icon: MessageSquare,
      title: "WhatsApp Assistant",
      description: "Get AI assistance and share updates via WhatsApp messaging"
    },
    {
      icon: Users,
      title: "Contact Management",
      description: "Organize and manage your business contacts with smart categorization"
    },
    {
      icon: Zap,
      title: "Task Automation",
      description: "Automatically extract and track tasks from meetings, emails, and calls"
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Enterprise-grade security with end-to-end encryption for all your data"
    }
  ];

  const stats = [
    { number: "10K+", label: "Active Users" },
    { number: "50K+", label: "Tasks Completed" },
    { number: "99.9%", label: "Uptime" },
    { number: "24/7", label: "AI Support" }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="minimal-container py-20">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="minimal-heading minimal-heading-xl mb-6 text-5xl font-bold">
              Your AI Personal Assistant
              <span className="block text-blue-600">for Business</span>
            </h1>
            <p className="minimal-text text-xl mb-8 text-gray-600 max-w-2xl mx-auto">
              Streamline your workflow with intelligent calendar management, 
              email insights, and automated task tracking designed for MSME business owners.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              {user ? (
                <Link
                  to="/dashboard"
                  className="minimal-button minimal-button-primary text-lg px-8 py-4"
                >
                  Go to Dashboard
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Link>
              ) : (
                <>
                  <Link
                    to="/signup"
                    className="minimal-button minimal-button-primary text-lg px-8 py-4"
                  >
                    Get Started Free
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Link>
                  <Link
                    to="/login"
                    className="minimal-button minimal-button-secondary text-lg px-8 py-4"
                  >
                    Sign In
                  </Link>
                </>
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-2xl mx-auto">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="minimal-heading minimal-heading-lg text-2xl font-bold text-blue-600 mb-1">
                    {stat.number}
                  </div>
                  <div className="minimal-text-secondary">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="minimal-container">
          <div className="text-center mb-16">
            <h2 className="minimal-heading minimal-heading-xl mb-4">
              Everything you need to stay organized
            </h2>
            <p className="minimal-text text-lg text-gray-600 max-w-2xl mx-auto">
              Powerful features designed to help you manage your business more efficiently
            </p>
          </div>

          <div className="minimal-grid minimal-grid-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="minimal-card p-8 text-center hover:shadow-lg transition-shadow">
                  <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <Icon className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="minimal-heading minimal-heading-md mb-4">{feature.title}</h3>
                  <p className="minimal-text-secondary">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20">
        <div className="minimal-container">
          <div className="text-center mb-16">
            <h2 className="minimal-heading minimal-heading-xl mb-4">
              How it works
            </h2>
            <p className="minimal-text text-lg text-gray-600">
              Get started in minutes with our simple 3-step process
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-6 text-xl font-bold">
                1
              </div>
              <h3 className="minimal-heading minimal-heading-md mb-4">Connect Your Accounts</h3>
              <p className="minimal-text-secondary">
                Link your Google Calendar, Gmail, and WhatsApp to get started
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-6 text-xl font-bold">
                2
              </div>
              <h3 className="minimal-heading minimal-heading-md mb-4">AI Learns Your Patterns</h3>
              <p className="minimal-text-secondary">
                Our AI analyzes your schedule and preferences to provide personalized assistance
              </p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-6 text-xl font-bold">
                3
              </div>
              <h3 className="minimal-heading minimal-heading-md mb-4">Stay Productive</h3>
              <p className="minimal-text-secondary">
                Get intelligent reminders, automated task extraction, and smart scheduling
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600">
        <div className="minimal-container text-center">
          <h2 className="minimal-heading minimal-heading-xl mb-4 text-white">
            Ready to transform your productivity?
          </h2>
          <p className="minimal-text text-xl mb-8 text-blue-100 max-w-2xl mx-auto">
            Join thousands of business owners who are already using AI to stay organized and focused.
          </p>
          
          {user ? (
            <Link
              to="/dashboard"
              className="minimal-button bg-white text-blue-600 hover:bg-gray-100 text-lg px-8 py-4"
            >
              Go to Dashboard
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          ) : (
            <Link
              to="/signup"
              className="minimal-button bg-white text-blue-600 hover:bg-gray-100 text-lg px-8 py-4"
            >
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-gray-900">
        <div className="minimal-container">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">PA</span>
              </div>
              <span className="minimal-heading text-white">ProjectAria.PA</span>
            </div>
            <div className="minimal-text-secondary text-gray-400">
              © 2025 ProjectAria.PA. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
