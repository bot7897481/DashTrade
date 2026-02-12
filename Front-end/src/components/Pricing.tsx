import { motion } from "framer-motion";
import { Check, Sparkles } from "lucide-react";

const Pricing = () => {
  const plans = [
    {
      name: "Free Beta",
      price: "$0",
      period: "forever during beta",
      description: "Everything you need to start automated trading.",
      features: [
        "Unlimited trading bots",
        "TradingView webhook integration",
        "Real-time dashboard",
        "Encrypted API storage",
        "Paper & live trading",
        "Discord support",
      ],
      cta: "Start Free",
      featured: true,
    },
    {
      name: "Pro",
      price: "$29",
      period: "per month",
      description: "Advanced features for serious traders.",
      features: [
        "Everything in Free",
        "System strategies library",
        "Priority execution",
        "Advanced analytics",
        "Outgoing webhooks",
        "Priority support",
      ],
      cta: "Coming Soon",
      featured: false,
      disabled: true,
    },
  ];

  return (
    <section id="pricing" className="relative py-24 lg:py-32">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-medium mb-6">
            <span className="text-gradient-gold">Simple,</span>{" "}
            <span className="text-foreground">transparent pricing</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto font-sans">
            Start for free. Upgrade when you're ready for more power.
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative rounded-3xl p-8 ${
                plan.featured
                  ? "bg-gradient-to-b from-card to-background border-2 border-primary/30 glow-cyan"
                  : "bg-card border border-border"
              }`}
            >
              {/* Featured Badge */}
              {plan.featured && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <div className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-primary text-primary-foreground text-sm font-medium">
                    <Sparkles className="w-4 h-4" />
                    Popular
                  </div>
                </div>
              )}

              {/* Plan Info */}
              <div className="text-center mb-8">
                <h3 className="font-display text-2xl font-semibold text-foreground mb-2">
                  {plan.name}
                </h3>
                <div className="flex items-baseline justify-center gap-1 mb-2">
                  <span className="font-display text-5xl font-bold text-foreground">
                    {plan.price}
                  </span>
                  <span className="text-muted-foreground font-sans text-sm">
                    /{plan.period}
                  </span>
                </div>
                <p className="text-muted-foreground font-sans text-sm">
                  {plan.description}
                </p>
              </div>

              {/* Features */}
              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/20 flex items-center justify-center">
                      <Check className="w-3 h-3 text-primary" />
                    </div>
                    <span className="text-foreground font-sans text-sm">
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <button
                disabled={plan.disabled}
                className={`w-full py-3.5 rounded-full font-medium font-sans transition-all duration-300 ${
                  plan.featured
                    ? "hero-button-primary"
                    : "hero-button-secondary opacity-50 cursor-not-allowed"
                }`}
              >
                {plan.cta}
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Pricing;
