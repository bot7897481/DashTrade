import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { ArrowRight, Bot, TrendingUp, Shield, Zap } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

const Hero = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredWord, setHoveredWord] = useState<string | null>(null);
  
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  const springConfig = { damping: 25, stiffness: 150 };
  const x = useSpring(mouseX, springConfig);
  const y = useSpring(mouseY, springConfig);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    mouseX.set((e.clientX - rect.left - centerX) / 20);
    mouseY.set((e.clientY - rect.top - centerY) / 20);
  };

  const stats = [
    { value: "24/7", label: "Automated Trading" },
    { value: "0.1s", label: "Execution Speed" },
    { value: "100%", label: "Strategy Compliant" },
  ];

  // Trading-inspired chart lines
  const chartLines = Array.from({ length: 8 }, (_, i) => ({
    id: i,
    delay: i * 0.15,
    startY: 40 + Math.random() * 20,
  }));

  return (
    <section 
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden"
    >
      {/* Animated Background Grid */}
      <motion.div 
        style={{ x, y }}
        className="absolute inset-0 bg-[linear-gradient(to_right,hsl(220_15%_15%/0.3)_1px,transparent_1px),linear-gradient(to_bottom,hsl(220_15%_15%/0.3)_1px,transparent_1px)] bg-[size:60px_60px]" 
      />

      {/* Dynamic Gradient that follows mouse */}
      <motion.div 
        style={{ 
          x: useTransform(x, v => v * 3),
          y: useTransform(y, v => v * 3),
        }}
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,hsl(185_90%_50%/0.12),transparent_50%)]" 
      />

      {/* Trading Chart Lines - appear on hover */}
      <svg 
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ opacity: hoveredWord ? 1 : 0.3, transition: 'opacity 0.5s ease' }}
      >
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="hsl(185 90% 50% / 0)" />
            <stop offset="50%" stopColor="hsl(185 90% 50% / 0.6)" />
            <stop offset="100%" stopColor="hsl(185 90% 50% / 0)" />
          </linearGradient>
          <linearGradient id="candleGreen" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="hsl(145 80% 50% / 0.8)" />
            <stop offset="100%" stopColor="hsl(145 80% 40% / 0.4)" />
          </linearGradient>
          <linearGradient id="candleRed" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="hsl(0 80% 50% / 0.8)" />
            <stop offset="100%" stopColor="hsl(0 80% 40% / 0.4)" />
          </linearGradient>
        </defs>
        
        {/* Animated trading lines */}
        {chartLines.map((line) => (
          <motion.path
            key={line.id}
            d={`M 0 ${line.startY}% Q 25% ${line.startY + (Math.random() - 0.5) * 30}%, 50% ${line.startY + (Math.random() - 0.5) * 20}% T 100% ${line.startY + (Math.random() - 0.5) * 25}%`}
            fill="none"
            stroke="url(#lineGradient)"
            strokeWidth="1.5"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={hoveredWord ? { 
              pathLength: 1, 
              opacity: 0.6,
              transition: { duration: 1.5, delay: line.delay, ease: "easeOut" }
            } : { 
              pathLength: 0, 
              opacity: 0,
              transition: { duration: 0.5 }
            }}
          />
        ))}

        {/* Candlestick patterns */}
        {hoveredWord && Array.from({ length: 12 }).map((_, i) => {
          const xPos = 8 + i * 8;
          const isGreen = Math.random() > 0.4;
          const height = 20 + Math.random() * 60;
          const yPos = 30 + Math.random() * 40;
          
          return (
            <motion.g key={`candle-${i}`}>
              {/* Wick */}
              <motion.line
                x1={`${xPos}%`}
                y1={`${yPos - 5}%`}
                x2={`${xPos}%`}
                y2={`${yPos + height / 100 * 15 + 5}%`}
                stroke={isGreen ? "hsl(145 60% 50% / 0.4)" : "hsl(0 60% 50% / 0.4)"}
                strokeWidth="1"
                initial={{ scaleY: 0, opacity: 0 }}
                animate={{ scaleY: 1, opacity: 0.5 }}
                transition={{ duration: 0.4, delay: 0.3 + i * 0.08 }}
              />
              {/* Body */}
              <motion.rect
                x={`${xPos - 0.8}%`}
                y={`${yPos}%`}
                width="1.6%"
                height={`${height / 100 * 8}%`}
                fill={isGreen ? "url(#candleGreen)" : "url(#candleRed)"}
                rx="2"
                initial={{ scaleY: 0, opacity: 0 }}
                animate={{ scaleY: 1, opacity: 0.7 }}
                transition={{ duration: 0.5, delay: 0.2 + i * 0.08 }}
                style={{ transformOrigin: 'center bottom' }}
              />
            </motion.g>
          );
        })}
      </svg>

      {/* Particle effect on hover */}
      {hoveredWord && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {Array.from({ length: 20 }).map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 rounded-full bg-primary"
              initial={{ 
                x: "50%", 
                y: "40%", 
                opacity: 0,
                scale: 0 
              }}
              animate={{ 
                x: `${20 + Math.random() * 60}%`, 
                y: `${20 + Math.random() * 60}%`,
                opacity: [0, 1, 0],
                scale: [0, 1.5, 0]
              }}
              transition={{ 
                duration: 2 + Math.random(),
                delay: Math.random() * 0.5,
                repeat: Infinity,
                repeatDelay: Math.random() * 2
              }}
            />
          ))}
        </div>
      )}

      {/* Secondary Gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_right,hsl(40_70%_55%/0.05),transparent_50%)]" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-border bg-card/50 backdrop-blur-sm mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span className="text-sm text-muted-foreground font-sans">
              Now in Public Beta — Free to Use
            </span>
          </motion.div>

          {/* Main Headline with Interactive Words */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-medium tracking-tight mb-6"
          >
            <span className="relative inline-block">
              <motion.span 
                className="text-gradient-gold cursor-pointer relative z-10"
                onMouseEnter={() => setHoveredWord('trade')}
                onMouseLeave={() => setHoveredWord(null)}
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                Trade
              </motion.span>
              {hoveredWord === 'trade' && (
                <motion.span
                  className="absolute -inset-4 bg-primary/10 rounded-2xl -z-0"
                  layoutId="highlight"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                />
              )}
            </span>{" "}
            <span className="text-foreground">Smarter,</span>
            <br />
            <span className="text-foreground">Not </span>
            <span className="relative inline-block">
              <motion.span 
                className="text-gradient-gold cursor-pointer relative z-10"
                onMouseEnter={() => setHoveredWord('harder')}
                onMouseLeave={() => setHoveredWord(null)}
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                Harder
              </motion.span>
              {hoveredWord === 'harder' && (
                <motion.span
                  className="absolute -inset-4 bg-secondary/10 rounded-2xl -z-0"
                  layoutId="highlight"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                />
              )}
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 font-sans leading-relaxed"
          >
            Connect TradingView to Alpaca and execute your strategies automatically. 
            No more missed trades. No more emotional decisions. Just pure, 
            algorithmic precision.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <Link to="/auth">
              <motion.button 
                className="hero-button-primary flex items-center gap-2 text-base"
                whileHover={{ scale: 1.02, boxShadow: "0 0 30px hsl(45 30% 90% / 0.4)" }}
                whileTap={{ scale: 0.98 }}
              >
                Start Trading Free
                <ArrowRight className="w-5 h-5" />
              </motion.button>
            </Link>
            <motion.button 
              className="hero-button-secondary flex items-center gap-2 text-base"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Watch Demo
            </motion.button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="grid grid-cols-3 gap-8 max-w-lg mx-auto"
          >
            {stats.map((stat, index) => (
              <motion.div 
                key={index} 
                className="text-center"
                whileHover={{ scale: 1.1 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                <div className="text-2xl sm:text-3xl font-display font-semibold text-foreground mb-1">
                  {stat.value}
                </div>
                <div className="text-xs sm:text-sm text-muted-foreground font-sans">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Floating Elements */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="absolute top-1/4 left-8 lg:left-16 hidden lg:block"
          style={{ 
            x: useTransform(x, v => v * -2),
            y: useTransform(y, v => v * -2),
          }}
        >
          <motion.div 
            className="feature-card p-4"
            animate={{ y: [0, -20, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          >
            <Bot className="w-8 h-8 text-primary" />
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="absolute top-1/3 right-8 lg:right-16 hidden lg:block"
          style={{ 
            x: useTransform(x, v => v * 2),
            y: useTransform(y, v => v * 2),
          }}
        >
          <motion.div 
            className="feature-card p-4"
            animate={{ y: [0, -20, 0] }}
            transition={{ duration: 6, delay: 1, repeat: Infinity, ease: "easeInOut" }}
          >
            <TrendingUp className="w-8 h-8 text-secondary" />
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.7 }}
          className="absolute bottom-1/4 left-16 lg:left-32 hidden lg:block"
          style={{ 
            x: useTransform(x, v => v * -1.5),
            y: useTransform(y, v => v * 1.5),
          }}
        >
          <motion.div 
            className="feature-card p-4"
            animate={{ y: [0, -20, 0] }}
            transition={{ duration: 6, delay: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <Shield className="w-8 h-8 text-primary" />
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="absolute bottom-1/3 right-16 lg:right-32 hidden lg:block"
          style={{ 
            x: useTransform(x, v => v * 1.5),
            y: useTransform(y, v => v * -1.5),
          }}
        >
          <motion.div 
            className="feature-card p-4"
            animate={{ y: [0, -20, 0] }}
            transition={{ duration: 6, delay: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <Zap className="w-8 h-8 text-secondary" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default Hero;
