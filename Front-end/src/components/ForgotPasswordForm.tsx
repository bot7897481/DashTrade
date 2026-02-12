import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast.ts';
import { api } from '@/lib/api.ts';
import { Loader2, ArrowLeft, CheckCircle, Mail } from 'lucide-react';
import { z } from 'zod';

const emailSchema = z.string().email('Please enter a valid email address');

interface ForgotPasswordFormProps {
  onBack: () => void;
}

export default function ForgotPasswordForm({ onBack }: ForgotPasswordFormProps) {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSent, setIsSent] = useState(false);
  const [error, setError] = useState('');
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      emailSchema.parse(email);
    } catch (err) {
      if (err instanceof z.ZodError) {
        setError(err.errors[0].message);
      }
      return;
    }

    setIsLoading(true);
    try {
      await api.forgotPassword(email);
      setIsSent(true);
    } catch (err) {
      // Still show success to prevent email enumeration
      setIsSent(true);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSent) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center"
      >
        <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
          <Mail className="h-6 w-6 text-primary" />
        </div>
        <h2 className="text-2xl font-display font-semibold text-foreground mb-2">Check Your Email</h2>
        <p className="text-muted-foreground mb-6">
          If an account exists for <span className="text-foreground font-medium">{email}</span>, we've sent a password reset link.
        </p>
        <button
          type="button"
          onClick={onBack}
          className="flex items-center justify-center gap-2 mx-auto text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Login</span>
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <div className="mb-6">
        <h2 className="text-2xl font-display font-semibold text-foreground">Forgot Password</h2>
        <p className="text-muted-foreground mt-1">
          Enter your email and we'll send you a reset link.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="forgot-email" className="text-foreground">Email Address</Label>
          <Input
            id="forgot-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="john@example.com"
            className="mt-1.5 bg-muted border-border focus:border-primary"
            disabled={isLoading}
          />
          {error && <p className="text-destructive text-sm mt-1">{error}</p>}
        </div>

        <Button type="submit" className="w-full hero-button-primary" disabled={isLoading}>
          {isLoading ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Sending...</>
          ) : (
            'Send Reset Link'
          )}
        </Button>
      </form>

      <button
        type="button"
        onClick={onBack}
        className="flex items-center justify-center gap-2 mx-auto mt-6 text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Login</span>
      </button>
    </motion.div>
  );
}
