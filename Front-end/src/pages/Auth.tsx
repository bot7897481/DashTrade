import React, { useState } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext.tsx';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast.ts';
import { Loader2, Eye, EyeOff, TrendingUp, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { z } from 'zod';
import ForgotPasswordForm from '@/components/ForgotPasswordForm';

const loginSchema = z.object({
  identifier: z.string()
    .min(3, 'Please enter a valid username or email')
    .refine(
      (val) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        // Valid if it's an email OR at least 3 chars (username)
        return emailRegex.test(val) || val.length >= 3;
      },
      { message: 'Please enter a valid username or email address' }
    ),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  full_name: z.string().min(2, 'Full name must be at least 2 characters'),
});

type AuthMode = 'login' | 'register' | 'forgot';

export default function Auth() {
  const [mode, setMode] = useState<AuthMode>('login');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  // Form fields
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');

  const { login, register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  const validateForm = () => {
    setErrors({});
    try {
      if (mode === 'login') {
        // Map username state to identifier for validation
        loginSchema.parse({ identifier: username, password });
      } else {
        registerSchema.parse({ username, email, password, full_name: fullName });
      }
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: Record<string, string> = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            // Map identifier errors back to username for display
            const field = err.path[0] === 'identifier' ? 'username' : err.path[0] as string;
            newErrors[field] = err.message;
          }
        });
        setErrors(newErrors);
      }
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      if (mode === 'login') {
        await login({ username, password });
        toast({
          title: 'Welcome back!',
          description: 'You have successfully logged in.',
        });
      } else {
        await register({ username, email, password, full_name: fullName });
        toast({
          title: 'Account created!',
          description: 'Welcome to NovAlgo.',
        });
      }
      navigate(from, { replace: true });
    } catch (error) {
      toast({
        title: mode === 'login' ? 'Login failed' : 'Registration failed',
        description: error instanceof Error ? error.message : 'An error occurred',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setErrors({});
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div 
          className="absolute inset-0"
          style={{ background: 'var(--gradient-hero)' }}
        />
        <div className="absolute inset-0 flex flex-col items-center justify-center p-12 z-10">
          <Link to="/" className="absolute top-8 left-8 flex items-center gap-2 text-foreground hover:text-primary transition-colors">
            <ArrowLeft className="h-5 w-5" />
            <span>Back to Home</span>
          </Link>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <div className="flex items-center justify-center gap-3 mb-6">
              <div className="p-3 rounded-xl bg-primary/10 glow-cyan">
                <TrendingUp className="h-10 w-10 text-primary" />
              </div>
            </div>
            <h1 className="text-5xl font-display font-bold text-gradient-gold mb-4">
              NovAlgo
            </h1>
            <p className="text-xl text-muted-foreground max-w-md">
              Automated trading signals, executed with precision.
            </p>
          </motion.div>

          {/* Decorative elements */}
          <div className="absolute bottom-0 left-0 right-0 h-64 bg-gradient-to-t from-background/50 to-transparent" />
        </div>
      </div>

      {/* Right side - Auth form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="p-2 rounded-lg bg-primary/10">
              <TrendingUp className="h-6 w-6 text-primary" />
            </div>
            <span className="text-2xl font-display font-bold text-gradient-gold">NovAlgo</span>
          </div>

          <div className="feature-card p-8">
            {mode === 'forgot' ? (
              <ForgotPasswordForm onBack={() => setMode('login')} />
            ) : (
              <>
                <div className="mb-6">
                  <h2 className="text-2xl font-display font-semibold text-foreground">
                    {mode === 'login' ? 'Welcome back' : 'Create account'}
                  </h2>
                  <p className="text-muted-foreground mt-1">
                    {mode === 'login' 
                      ? 'Enter your credentials to access your dashboard'
                      : 'Start automating your trading today'}
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <AnimatePresence mode="wait">
                    {mode === 'register' && (
                      <motion.div
                        key="fullname"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <Label htmlFor="fullName" className="text-foreground">Full Name</Label>
                        <Input
                          id="fullName"
                          type="text"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          placeholder="John Doe"
                          className="mt-1.5 bg-muted border-border focus:border-primary"
                          disabled={isLoading}
                        />
                        {errors.full_name && (
                          <p className="text-destructive text-sm mt-1">{errors.full_name}</p>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div>
                    <Label htmlFor="username" className="text-foreground">
                      {mode === 'login' ? 'Username or Email' : 'Username'}
                    </Label>
                    <Input
                      id="username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder={mode === 'login' ? 'johndoe or john@example.com' : 'johndoe'}
                      className="mt-1.5 bg-muted border-border focus:border-primary"
                      disabled={isLoading}
                    />
                    {errors.username && (
                      <p className="text-destructive text-sm mt-1">{errors.username}</p>
                    )}
                  </div>

                  <AnimatePresence mode="wait">
                    {mode === 'register' && (
                      <motion.div
                        key="email"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <Label htmlFor="email" className="text-foreground">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="john@example.com"
                          className="mt-1.5 bg-muted border-border focus:border-primary"
                          disabled={isLoading}
                        />
                        {errors.email && (
                          <p className="text-destructive text-sm mt-1">{errors.email}</p>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password" className="text-foreground">Password</Label>
                      {mode === 'login' && (
                        <button
                          type="button"
                          onClick={() => setMode('forgot')}
                          className="text-sm text-primary hover:text-primary/80 transition-colors"
                        >
                          Forgot password?
                        </button>
                      )}
                    </div>
                    <div className="relative mt-1.5">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="bg-muted border-border focus:border-primary pr-10"
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    {errors.password && (
                      <p className="text-destructive text-sm mt-1">{errors.password}</p>
                    )}
                  </div>

                  <Button
                    type="submit"
                    className="w-full hero-button-primary"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {mode === 'login' ? 'Signing in...' : 'Creating account...'}
                      </>
                    ) : (
                      mode === 'login' ? 'Sign In' : 'Create Account'
                    )}
                  </Button>
                </form>

                <div className="mt-6 text-center">
                  <p className="text-muted-foreground">
                    {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
                    <button
                      type="button"
                      onClick={switchMode}
                      className="ml-2 text-primary hover:text-primary/80 transition-colors font-medium"
                      disabled={isLoading}
                    >
                      {mode === 'login' ? 'Sign up' : 'Sign in'}
                    </button>
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Mobile back link */}
          <Link 
            to="/" 
            className="lg:hidden flex items-center justify-center gap-2 mt-6 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Home</span>
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
