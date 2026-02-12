import { motion } from "framer-motion";
import { UserPlus, Link2, Bot, Rocket } from "lucide-react";

const HowItWorks = () => {
  const steps = [
    {
      icon: UserPlus,
      title: "Create Account",
      description: "Sign up in seconds. No credit card required during beta.",
    },
    {
      icon: Link2,
      title: "Connect Alpaca",
      description: "Enter your Alpaca API keys. We encrypt them with bank-grade security.",
    },
    {
      icon: Bot,
      title: "Configure Bots",
      description: "Set up your trading bots with symbols, timeframes, and position sizes.",
    },
    {
      icon: Rocket,
      title: "Automate Trading",
      description: "Copy your webhook URL to TradingView and let the automation begin.",
    },
  ];

  return (
    <section id="how-it-works" className="relative py-24 lg:py-32 overflow-hidden">
      {/* Background Accent */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(40_70%_55%/0.03),transparent_70%)]" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-medium mb-6">
            <span className="text-gradient-gold">How it</span>{" "}
            <span className="text-foreground">works</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-sans">
            From sign-up to your first automated trade in under 5 minutes.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="relative">
          {/* Connecting Line */}
          <div className="hidden lg:block absolute top-24 left-1/2 -translate-x-1/2 w-3/4 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-6">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative text-center"
              >
                {/* Step Number */}
                <div className="relative inline-flex mb-6">
                  <div className="step-number">
                    {index + 1}
                  </div>
                  <div className="absolute -inset-3 rounded-full bg-primary/10 animate-pulse-slow" />
                </div>

                {/* Icon */}
                <div className="w-16 h-16 mx-auto mb-5 rounded-2xl bg-card border border-border flex items-center justify-center">
                  <step.icon className="w-8 h-8 text-secondary" />
                </div>

                {/* Content */}
                <h3 className="font-display text-xl font-semibold text-foreground mb-3">
                  {step.title}
                </h3>
                <p className="text-muted-foreground font-sans leading-relaxed">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center mt-16"
        >
          <button className="hero-button-primary">
            Get Started Now
          </button>
        </motion.div>
      </div>
    </section>
  );
};

export default HowItWorks;
