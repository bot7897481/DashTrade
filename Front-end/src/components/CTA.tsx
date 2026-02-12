import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const CTA = () => {
  return (
    <section className="relative py-24 lg:py-32 overflow-hidden">
      {/* Decorative Background Lines */}
      <div className="absolute inset-0">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute h-px bg-gradient-to-r from-transparent via-gold-muted/20 to-transparent"
            style={{
              top: `${5 + i * 5}%`,
              left: 0,
              right: 0,
              transform: `rotate(${-5 + i * 0.5}deg)`,
            }}
          />
        ))}
      </div>

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="font-display text-4xl sm:text-5xl lg:text-6xl font-medium mb-6">
            <span className="text-gradient-gold">Discover the power</span>
            <br />
            <span className="text-foreground">of automation</span>
          </h2>

          <p className="text-lg text-muted-foreground max-w-xl mx-auto mb-10 font-sans">
            Join thousands of traders who are already automating their strategies 
            with NovAlgo. Start your journey today.
          </p>

          <button className="hero-button-primary inline-flex items-center gap-2 text-base">
            Start Trading Free
            <ArrowRight className="w-5 h-5" />
          </button>
        </motion.div>
      </div>
    </section>
  );
};

export default CTA;
