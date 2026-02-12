import { motion } from "framer-motion";
import { Bot, Zap, Shield, BarChart3 } from "lucide-react";

const Features = () => {
  const features = [
    {
      icon: Bot,
      title: "Automated Execution",
      description:
        "Your TradingView alerts trigger instant trades on Alpaca. Sleep while your bots work around the clock.",
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      description:
        "Sub-second execution from signal to order. Never miss an entry or exit point again.",
    },
    {
      icon: Shield,
      title: "Bank-Grade Security",
      description:
        "256-bit Fernet encryption for your API keys. Trading-only permissions — no withdrawal access.",
    },
    {
      icon: BarChart3,
      title: "Real-Time Dashboard",
      description:
        "Monitor positions, P&L, and bot status in real-time. Complete visibility into your automated trading.",
    },
  ];

  return (
    <section id="features" className="relative py-24 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-medium mb-6">
            <span className="text-gradient-gold">Start trading</span>
            <br />
            <span className="text-foreground">like a pro</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-sans">
            Access institutional-grade automation tools designed for retail traders.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 gap-6 lg:gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="feature-card group"
            >
              <div className="flex items-start gap-5">
                <div className="flex-shrink-0">
                  <div className="w-14 h-14 rounded-2xl bg-muted/50 flex items-center justify-center group-hover:bg-primary/10 transition-colors duration-300">
                    <feature.icon className="w-7 h-7 text-primary" />
                  </div>
                </div>
                <div>
                  <h3 className="font-display text-xl font-semibold text-foreground mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-muted-foreground font-sans leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>

              {/* Decorative Line */}
              <div className="mt-6 h-px bg-gradient-to-r from-transparent via-border to-transparent" />

              {/* Learn More Link */}
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground font-sans group-hover:text-primary transition-colors">
                <span className="w-4 h-4 rounded-full border border-current flex items-center justify-center text-[10px]">
                  i
                </span>
                <span>Learn more</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
