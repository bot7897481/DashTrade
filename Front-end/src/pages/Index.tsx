import { Helmet } from "react-helmet-async";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import HowItWorks from "@/components/HowItWorks";
import Pricing from "@/components/Pricing";
import FAQ from "@/components/FAQ";
import CTA from "@/components/CTA";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <>
      <Helmet>
        <title>NovAlgo - Automated Trading Platform | TradingView to Alpaca</title>
        <meta
          name="description"
          content="Connect TradingView to Alpaca and automate your trading strategies. Execute trades automatically with bank-grade security. Start trading smarter, not harder."
        />
        <meta
          name="keywords"
          content="automated trading, TradingView, Alpaca, trading bot, algorithmic trading, webhook trading"
        />
      </Helmet>

      <div className="min-h-screen bg-background">
        <Navbar />
        <main>
          <Hero />
          <Features />
          <HowItWorks />
          <Pricing />
          <FAQ />
          <CTA />
        </main>
        <Footer />
      </div>
    </>
  );
};

export default Index;
