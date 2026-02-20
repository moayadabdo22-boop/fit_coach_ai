import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Dumbbell, MessageCircle, User, Globe, Calendar, LogOut, LogIn } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';

export function Navbar() {
  const { t, language, setLanguage } = useLanguage();
  const { user, signOut } = useAuth();
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: t('nav.home') },
    { path: '/workouts', icon: Dumbbell, label: t('nav.workouts') },
    { path: '/coach', icon: MessageCircle, label: t('nav.coach') },
    { path: '/schedule', icon: Calendar, label: language === 'ar' ? 'الجدول' : 'Schedule' },
    { path: '/profile', icon: User, label: t('nav.profile') },
  ];

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'ar' : 'en');
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-border/50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
              <Dumbbell className="w-6 h-6 text-primary-foreground" />
            </div>
            <span className="font-display text-2xl tracking-wide text-foreground">
              FITCOACH
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link key={item.path} to={item.path}>
                  <Button
                    variant={isActive ? 'default' : 'ghost'}
                    className={`relative ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </div>

          {/* Right section */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleLanguage}
              className="border-border/50 text-muted-foreground hover:text-foreground"
            >
              <Globe className="w-4 h-4 mr-1" />
              {language === 'en' ? 'عربي' : 'EN'}
            </Button>
            
            {user ? (
              <Button variant="ghost" size="sm" onClick={signOut} className="hidden md:flex text-muted-foreground hover:text-foreground">
                <LogOut className="w-4 h-4 mr-1" />
                {language === 'ar' ? 'خروج' : 'Logout'}
              </Button>
            ) : (
              <Link to="/auth">
                <Button variant="ghost" size="sm" className="hidden md:flex text-muted-foreground hover:text-foreground">
                  <LogIn className="w-4 h-4 mr-1" />
                  {language === 'ar' ? 'دخول' : 'Login'}
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 glass-card border-t border-border/50 px-2 py-1.5">
        <div className="flex justify-around">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link key={item.path} to={item.path}>
                <Button
                  variant="ghost"
                  size="sm"
                  className={`flex flex-col items-center gap-0.5 h-auto py-1.5 px-2 ${
                    isActive ? 'text-primary' : 'text-muted-foreground'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="text-[10px]">{item.label}</span>
                </Button>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
