import { motion } from "framer-motion";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const FAQ = () => {
  const faqs = [
    {
      question: "What is NovAlgo and how does it work?",
      answer:
        "NovAlgo connects your TradingView charts to your Alpaca brokerage account. When your TradingView strategy generates a buy or sell signal, it sends a webhook to NovAlgo, which then automatically executes the trade on your behalf through the Alpaca API.",
    },
    {
      question: "Is my money safe? Can NovAlgo withdraw from my account?",
      answer:
        "Your funds are completely safe. NovAlgo only requires trading-level API permissions from Alpaca — this means we can place trades but have zero ability to withdraw funds. Additionally, all your API keys are encrypted with 256-bit Fernet encryption.",
    },
    {
      question: "Do I need coding experience to use NovAlgo?",
      answer:
        "No coding required! If you can create an alert in TradingView, you can use NovAlgo. Simply copy your unique webhook URL, paste it into your TradingView alert, and format your alert message as shown in our documentation.",
    },
    {
      question: "Can I test with paper trading before going live?",
      answer:
        "Absolutely! We strongly recommend testing with Alpaca's paper trading environment first. You can easily switch between paper and live trading in your bot settings.",
    },
    {
      question: "How fast are trades executed?",
      answer:
        "Trades are typically executed within 100-200 milliseconds of receiving the webhook from TradingView. This is significantly faster than any human could react to an alert.",
    },
    {
      question: "What happens if TradingView or NovAlgo goes down?",
      answer:
        "If our systems experience downtime, no new trades will be executed. Your existing positions remain safely in your Alpaca account. We recommend setting stop-losses directly in Alpaca as a backup safety measure.",
    },
    {
      question: "Is NovAlgo really free?",
      answer:
        "Yes! During our public beta, NovAlgo is completely free to use with no limitations. We'll introduce premium features in the future, but the core automation functionality will always have a free tier.",
    },
    {
      question: "Which brokerages are supported?",
      answer:
        "Currently, we support Alpaca, which offers commission-free trading and an excellent API. We're evaluating additional brokerage integrations based on user demand.",
    },
  ];

  return (
    <section id="faq" className="relative py-24 lg:py-32">
      {/* Background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom,hsl(185_90%_50%/0.05),transparent_60%)]" />

      <div className="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <h2 className="font-display text-4xl sm:text-5xl font-medium mb-6 text-foreground">
            Get to know all the benefits
          </h2>
        </motion.div>

        {/* FAQ Accordion */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem
                key={index}
                value={`item-${index}`}
                className="border-b border-border/50 pb-4"
              >
                <AccordionTrigger className="text-left font-sans text-foreground hover:text-primary transition-colors py-4 text-base sm:text-lg">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground font-sans leading-relaxed pb-4">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  );
};

export default FAQ;
