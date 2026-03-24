import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Dumbbell, MessageCircle, Target, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Navbar } from '@/components/layout/Navbar';
import { useLanguage } from '@/contexts/LanguageContext';
import { useUser } from '@/contexts/UserContext';
import { useAuth } from '@/hooks/useAuth';
import heroBg from '@/assets/hero-bg.jpg';

const Index = () => {
  const { t } = useLanguage();
  const { isOnboarded } = useUser();
  const { user } = useAuth();

  const features = [
    {
      icon: Target,
      title: 'Personalized Workouts',
      description: 'AI-powered exercise recommendations based on your goals and body type.',
    },
    {
      icon: Dumbbell,
      title: 'Home & Gym Ready',
      description: 'Exercises adapted for wherever you train - no equipment needed at home.',
    },
    {
      icon: MessageCircle,
      title: 'AI Coach 24/7',
      description: 'Get instant fitness advice, nutrition tips, and motivation anytime.',
    },
    {
      icon: Zap,
      title: 'Track Progress',
      description: 'Monitor your journey with smart analytics and personalized insights.',
    },
  ];

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <img
            src={heroBg}
            alt="Fitness hero"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-background/70 via-background/50 to-background" />
        </div>

        {/* Content */}
        <div className="relative z-10 container mx-auto px-4 text-center pt-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="font-display text-6xl md:text-8xl lg:text-9xl text-foreground mb-6 leading-none">
              {t('hero.title')}
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
              {t('hero.subtitle')}
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to={user ? (isOnboarded ? '/workouts' : '/onboarding') : '/auth?force=1'}
                className={cn(buttonVariants({ variant: 'hero', size: 'xl' }))}
              >
                {t('hero.cta')}
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
              <Link
                to={user ? '/workouts' : '/auth?force=1'}
                className={cn(buttonVariants({ variant: 'glass', size: 'xl' }))}
              >
                {t('hero.secondary')}
              </Link>
            </div>
          </motion.div>

          {/* Scroll Indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1, duration: 0.5 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2"
          >
            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-6 h-10 rounded-full border-2 border-muted-foreground/50 flex items-start justify-center p-2"
            >
              <div className="w-1.5 h-3 bg-primary rounded-full" />
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="font-display text-4xl md:text-5xl text-foreground mb-4">
              EVERYTHING YOU NEED
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              A complete fitness platform designed to help you achieve your goals
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="glass-card rounded-2xl p-6 text-center hover:border-primary/50 transition-all duration-300 group"
              >
                <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                  <feature.icon className="w-7 h-7 text-primary" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="glass-card rounded-3xl p-10 md:p-16 text-center glow-border"
          >
            <h2 className="font-display text-4xl md:text-6xl text-foreground mb-4">
              START YOUR TRANSFORMATION
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto mb-8">
              Join thousands of users who have achieved their fitness goals with our AI-powered coaching platform.
            </p>
            <a
              href={isOnboarded ? '/workouts' : '/onboarding'}
              className={cn(buttonVariants({ variant: 'hero', size: 'xl' }))}
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 ml-2" />
            </a>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/50 py-8 px-4">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-primary flex items-center justify-center">
              <Dumbbell className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-display text-xl">FITCOACH</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2026 FitCoach. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
