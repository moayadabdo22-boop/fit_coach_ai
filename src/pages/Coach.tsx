import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, User, Loader2, Mic, MicOff, Volume2, VolumeX, Plus, MessageSquare, Trash2, Menu, X, Settings2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Navbar } from '@/components/layout/Navbar';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { repairMojibake } from '@/lib/text';
import { useLanguage } from '@/contexts/LanguageContext';
import { useAuth } from '@/hooks/useAuth';
import { useUser } from '@/contexts/UserContext';
import { useVoiceChat, type VoiceChatApiResponse } from '@/hooks/useVoiceChat';
import { supabase } from '@/integrations/supabase/client';
import { PlanApprovalUI } from '@/components/ai/PlanApprovalUI';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  updated_at: string;
}

interface PendingPlanState {
  id: string;
  type: 'workout' | 'nutrition';
  plan: any;
}

const AI_BACKEND_URL = import.meta.env.VITE_AI_BACKEND_URL || 'http://127.0.0.1:8002';
const NUTRITION_PREFIX = '\u{1F37D}\uFE0F';
const WEEK_TEMPLATE = [
  { day: 'Saturday', dayAr: 'السبت' },
  { day: 'Sunday', dayAr: 'الأحد' },
  { day: 'Monday', dayAr: 'الاثنين' },
  { day: 'Tuesday', dayAr: 'الثلاثاء' },
  { day: 'Wednesday', dayAr: 'الأربعاء' },
  { day: 'Thursday', dayAr: 'الخميس' },
  { day: 'Friday', dayAr: 'الجمعة' },
];

export function CoachPage() {
  const { t, language } = useLanguage();
  const { user } = useAuth();
  const { profile } = useUser();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [currentMessages, setCurrentMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTypingReply, setIsTypingReply] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [pendingPlan, setPendingPlan] = useState<PendingPlanState | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<string>(() => {
    return localStorage.getItem('fitcoach_voice') || '';
  });
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [voiceMode, setVoiceMode] = useState(false);
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false);
  const [pendingVoiceResponse, setPendingVoiceResponse] = useState<VoiceChatApiResponse | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const voiceModeRef = useRef(false);
  const assistantAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    voiceModeRef.current = voiceMode;
  }, [voiceMode]);

  // Load available voices
  useEffect(() => {
    const loadVoices = () => {
      const voices = window.speechSynthesis?.getVoices() || [];
      setAvailableVoices(voices);
    };
    loadVoices();
    window.speechSynthesis?.addEventListener('voiceschanged', loadVoices);
    return () => window.speechSynthesis?.removeEventListener('voiceschanged', loadVoices);
  }, []);

  // Filter voices by language
  const filteredVoices = availableVoices.filter(v => {
    if (language === 'ar') return v.lang.startsWith('ar');
    return v.lang.startsWith('en');
  });

  const handleVoiceBackendResponse = useCallback(async (payload: VoiceChatApiResponse) => {
    setPendingVoiceResponse(payload);
  }, []);

  const {
    isListening,
    isProcessing: isVoiceProcessing,
    isSupported,
    error: voiceError,
    clearError,
    startListening,
    stopListening,
    cancelVoiceRequest,
  } = useVoiceChat({
    backendUrl: AI_BACKEND_URL,
    language,
    userId: user?.id,
    conversationId: currentId || user?.id || null,
    onResponse: handleVoiceBackendResponse,
  });
  const isBusy = isLoading || isVoiceProcessing;

  const startListeningIfPossible = useCallback(() => {
    if (!isSupported) return;
    if (isLoading || isVoiceProcessing || isListening || isAssistantSpeaking) return;
    clearError();
    startListening();
  }, [isSupported, isLoading, isVoiceProcessing, isListening, isAssistantSpeaking, clearError, startListening]);

  const stopAllSpeech = useCallback(() => {
    cancelVoiceRequest();
    if (assistantAudioRef.current) {
      try {
        assistantAudioRef.current.pause();
        assistantAudioRef.current.currentTime = 0;
      } catch {
        // ignore media stop errors
      }
    }
    window.speechSynthesis?.cancel();
    setIsAssistantSpeaking(false);
  }, [cancelVoiceRequest]);

  const speakWithVoice = useCallback((text: string) => {
    if (!('speechSynthesis' in window)) return;
    const cleanText = text
      .replace(/[#*_~`>]/g, '')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/```[\s\S]*?```/g, '')
      .replace(/\n+/g, '. ')
      .trim();

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(cleanText);

    if (selectedVoice && selectedVoice !== 'default') {
      const voice = availableVoices.find(v => v.name === selectedVoice);
      if (voice) utterance.voice = voice;
    } else {
      const langVoices = availableVoices.filter(v =>
        language === 'ar' ? v.lang.startsWith('ar') : v.lang.startsWith('en')
      );
      if (langVoices.length > 0) utterance.voice = langVoices[0];
      utterance.lang = language === 'ar' ? 'ar-SA' : 'en-US';
    }

    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.onstart = () => setIsAssistantSpeaking(true);
    utterance.onend = () => {
      setIsAssistantSpeaking(false);
      if (voiceModeRef.current) {
        window.setTimeout(() => startListeningIfPossible(), 250);
      }
    };
    utterance.onerror = () => setIsAssistantSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [language, selectedVoice, availableVoices, startListeningIfPossible]);

  const playBackendAudio = useCallback((relativePath?: string) => {
    if (!relativePath) {
      if (voiceModeRef.current) {
        window.setTimeout(() => startListeningIfPossible(), 250);
      }
      return;
    }

    const cleanPath = relativePath.startsWith('/') ? relativePath : `/${relativePath}`;
    const sourceUrl = `${AI_BACKEND_URL}${cleanPath}`;

    try {
      if (assistantAudioRef.current) {
        assistantAudioRef.current.pause();
        assistantAudioRef.current.currentTime = 0;
      }

      const audio = new Audio(sourceUrl);
      assistantAudioRef.current = audio;
      setIsAssistantSpeaking(true);

      audio.onended = () => {
        setIsAssistantSpeaking(false);
        if (voiceModeRef.current) {
          window.setTimeout(() => startListeningIfPossible(), 250);
        }
      };
      audio.onerror = () => {
        setIsAssistantSpeaking(false);
        if (voiceModeRef.current) {
          window.setTimeout(() => startListeningIfPossible(), 250);
        }
      };
      audio.play().catch(() => {
        setIsAssistantSpeaking(false);
        if (voiceModeRef.current) {
          window.setTimeout(() => startListeningIfPossible(), 250);
        }
      });
    } catch {
      setIsAssistantSpeaking(false);
      if (voiceModeRef.current) {
        window.setTimeout(() => startListeningIfPossible(), 250);
      }
    }
  }, [startListeningIfPossible]);

  const toggleVoiceMode = useCallback(() => {
    if (voiceModeRef.current) {
      setVoiceMode(false);
      stopListening();
      stopAllSpeech();
      return;
    }
    setVoiceMode(true);
    setAutoSpeak(true);
    window.setTimeout(() => startListeningIfPossible(), 120);
  }, [startListeningIfPossible, stopAllSpeech, stopListening]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentMessages]);

  useEffect(() => {
    if (!user) {
      setLoadingConvs(false);
      return;
    }
    loadConversations();
  }, [user]);

  useEffect(() => {
    return () => {
      stopAllSpeech();
      stopListening();
    };
  }, [stopAllSpeech, stopListening]);

  useEffect(() => {
    if (!pendingVoiceResponse || !user) return;

    const applyVoiceResponse = async () => {
      const transcript = (pendingVoiceResponse.transcript || '').trim();
      const reply = (pendingVoiceResponse.reply || '').trim();
      const now = Date.now();

      const userMessage: ChatMessage | null = transcript
        ? { role: 'user', content: transcript, timestamp: now }
        : null;
      const assistantMessage: ChatMessage | null = reply
        ? { role: 'assistant', content: reply, timestamp: now + 1 }
        : null;

      const additions = [userMessage, assistantMessage].filter(Boolean) as ChatMessage[];
      if (additions.length === 0) {
        setPendingVoiceResponse(null);
        return;
      }

      const updatedMessages = [...currentMessages, ...additions];
      setCurrentMessages(updatedMessages);
      setConversations(prev =>
        prev.map(c =>
          c.id === currentId
            ? { ...c, messages: updatedMessages, updated_at: new Date().toISOString() }
            : c
        )
      );

      if (currentId) {
        const rows: Array<{
          conversation_id: string;
          user_id: string;
          role: string;
          content: string;
        }> = [];
        if (userMessage) {
          rows.push({
            conversation_id: currentId,
            user_id: user.id,
            role: 'user',
            content: userMessage.content,
          });
        }
        if (assistantMessage) {
          rows.push({
            conversation_id: currentId,
            user_id: user.id,
            role: 'assistant',
            content: assistantMessage.content,
          });
        }
        if (rows.length > 0 && supabase && supabase.from) {
          try {
            await supabase.from('chat_messages').insert(rows as any);
          } catch (error) {
            console.warn('Failed to save messages to Supabase:', error);
            // لا نوقف التطبيق - الرسائل محفوظة محلياً بالفعل
          }
        }
      }

      if (reply && (voiceModeRef.current || autoSpeak)) {
        playBackendAudio(pendingVoiceResponse.audio_path);
      } else if (voiceModeRef.current) {
        window.setTimeout(() => startListeningIfPossible(), 250);
      }

      setPendingVoiceResponse(null);
    };

    applyVoiceResponse().catch((err) => {
      console.error('Failed to apply voice response:', err);
      setPendingVoiceResponse(null);
    });
  }, [
    autoSpeak,
    currentId,
    currentMessages,
    pendingVoiceResponse,
    playBackendAudio,
    startListeningIfPossible,
    user,
  ]);

  const loadConversations = async () => {
    if (!user) return;
    setLoadingConvs(true);
    
    try {
      if (!supabase || !supabase.from) {
        console.warn('Supabase not available');
        await createConversation();
        setLoadingConvs(false);
        return;
      }

      const { data: convs } = await supabase
        .from('chat_conversations')
        .select('*')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false });

      if (convs && convs.length > 0) {
        const convsWithMessages: Conversation[] = [];
        for (const conv of convs) {
          const { data: msgs } = await supabase
            .from('chat_messages')
            .select('*')
            .eq('conversation_id', conv.id)
            .order('created_at', { ascending: true });
          
          convsWithMessages.push({
            id: conv.id,
            title: conv.title,
            messages: (msgs || []).map(m => ({
              role: m.role as 'user' | 'assistant',
              content: m.content,
              timestamp: new Date(m.created_at).getTime(),
            })),
            updated_at: conv.updated_at,
          });
        }
        setConversations(convsWithMessages);
        setCurrentId(convsWithMessages[0].id);
        setCurrentMessages(convsWithMessages[0].messages);
      } else {
        await createConversation();
      }
    } catch (error) {
      console.warn('Failed to load conversations:', error);
      await createConversation();
    } finally {
      setLoadingConvs(false);
    }
  };

  const createConversation = async () => {
    if (!user) return;

    let id = (typeof crypto !== 'undefined' && 'randomUUID' in crypto)
      ? crypto.randomUUID()
      : `conv_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
    let updatedAt = new Date().toISOString();

    // حاول حفظ في Supabase إذا كانت متاحة
    if (supabase && supabase.from) {
      try {
        const { data, error } = await supabase
          .from('chat_conversations')
          .insert({ user_id: user.id, title: '' })
          .select('id, updated_at')
          .single();

        if (!error && data?.id) {
          id = data.id;
          updatedAt = data.updated_at || updatedAt;
        } else if (error) {
          console.warn('Supabase insert error, falling back to local id:', error);
        }
      } catch (error) {
        console.warn('Failed to create conversation in Supabase:', error);
      }
    }

    const newConv: Conversation = {
      id,
      title: '',
      messages: [],
      updated_at: updatedAt,
    };

    setConversations(prev => [newConv, ...prev]);
    setCurrentId(id);
    setCurrentMessages([]);
  };

  const selectConversation = (id: string) => {
    const conv = conversations.find(c => c.id === id);
    if (conv) {
      setCurrentId(id);
      setCurrentMessages(conv.messages);
      setPendingPlan(null);
    }
    setSidebarOpen(false);
  };

  const deleteConversation = async (id: string) => {
    if (supabase && supabase.from) {
      try {
        await supabase.from('chat_conversations').delete().eq('id', id);
      } catch (error) {
        console.warn('Failed to delete conversation from Supabase:', error);
      }
    }
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentId === id) {
      const remaining = conversations.filter(c => c.id !== id);
      if (remaining.length > 0) {
        setCurrentId(remaining[0].id);
        setCurrentMessages(remaining[0].messages);
      } else {
        setCurrentId(null);
        setCurrentMessages([]);
        await createConversation();
      }
    }
  };
  const formatExercisesMessage = (exercises: any[]) => {
    if (!Array.isArray(exercises) || exercises.length === 0) {
      return language === 'ar'
        ? 'لم أجد تمارين مناسبة في قاعدة البيانات. حاول صياغة طلبك بشكل مختلف.'
        : 'I could not find matching exercises in the knowledge base. Try rephrasing your request.';
    }

    return exercises
      .map((item, idx) =>
        [
          `${idx + 1}. ${item.exercise}`,
          `- Muscle: ${item.muscle}`,
          `- Difficulty: ${item.difficulty}`,
          `- Injury Safe: ${item.injury_safe ? 'Yes' : 'No'}`,
          `- ${item.description}`,
        ].join('\\n')
      )
      .join('\\n\\n');
  };

  const toWorkoutPlanData = (plan: any) => {
    if (Array.isArray(plan?.days) && plan.days.length > 0) {
      return plan.days;
    }

    const exercises = Array.isArray(plan?.exercises) ? plan.exercises : [];
    const workoutDayIndexes = [0, 2, 4]; // Saturday, Monday, Wednesday
    const grouped = workoutDayIndexes.map(() => [] as any[]);

    exercises.forEach((exercise: any, index: number) => {
      grouped[index % workoutDayIndexes.length].push(exercise);
    });

    return WEEK_TEMPLATE.map((weekDay, weekIndex) => {
      const slot = workoutDayIndexes.indexOf(weekIndex);
      const dayExercises = slot >= 0 ? grouped[slot] : [];
      return {
        ...weekDay,
        exercises: dayExercises.map((ex: any) => ({
          name: ex?.name || 'Exercise',
          nameAr: ex?.nameAr || ex?.name || 'تمرين',
          sets: String(ex?.sets ?? ''),
          reps: String(ex?.reps ?? ''),
        })),
      };
    });
  };

  const toNutritionPlanData = (plan: any) => {
    if (Array.isArray(plan?.days) && plan.days.length > 0) {
      return plan.days;
    }

    const meals = Array.isArray(plan?.meals) ? plan.meals : [];
    const mappedMeals = meals.map((meal: any) => ({
      name: meal?.name || 'Meal',
      nameAr: meal?.nameAr || meal?.name || 'وجبة',
      description: Array.isArray(meal?.ingredients) ? meal.ingredients.join(', ') : (meal?.description || ''),
      descriptionAr: meal?.descriptionAr || (Array.isArray(meal?.ingredients) ? meal.ingredients.join(', ') : (meal?.description || '')),
      calories: String(meal?.calories ?? ''),
    }));

    return WEEK_TEMPLATE.map((weekDay) => ({
      ...weekDay,
      meals: mappedMeals,
    }));
  };

  const extractPendingPlanFromResponse = (
    responseData: any
  ): PendingPlanState | null => {
    if (responseData?.action !== 'ask_plan' || !responseData?.data?.plan || !responseData?.data?.plan_id) {
      return null;
    }

    return {
      id: responseData.data.plan_id,
      type: responseData.data.plan_type === 'nutrition' ? 'nutrition' : 'workout',
      plan: responseData.data.plan,
    };
  };

  const extractApprovedPlanFromResponse = (
    responseData: any
  ): { type: 'workout' | 'nutrition'; plan: any } | null => {
    if (responseData?.approved_plan?.plan) {
      const approved = responseData.approved_plan;
      return {
        type: approved.type === 'meal' || approved.type === 'nutrition' ? 'nutrition' : 'workout',
        plan: approved.plan,
      };
    }

    if (responseData?.data?.approved_plan?.plan) {
      const approved = responseData.data.approved_plan;
      return {
        type: approved.type === 'meal' || approved.type === 'nutrition' ? 'nutrition' : 'workout',
        plan: approved.plan,
      };
    }

    return null;
  };

  const persistApprovedPlan = async (approvedPayload: any) => {
    if (!user) return;
    const extracted = extractApprovedPlanFromResponse(approvedPayload);
    if (!extracted) return;

    const { type, plan } = extracted;
    const planData = type === 'nutrition' ? toNutritionPlanData(plan) : toWorkoutPlanData(plan);
    if (!Array.isArray(planData) || planData.length === 0) return;

    const title = type === 'nutrition'
      ? `${NUTRITION_PREFIX} ${plan?.title || 'Nutrition Plan'}`
      : (plan?.title || 'AI Workout Plan');
    const title_ar = plan?.title_ar || (type === 'nutrition' ? 'خطة تغذية' : 'خطة تمارين');

    if (type === 'nutrition') {
      await supabase.from('workout_plans').update({ is_active: false })
        .eq('user_id', user.id)
        .like('title', `${NUTRITION_PREFIX}%`);
    } else {
      await supabase.from('workout_plans').update({ is_active: false })
        .eq('user_id', user.id)
        .not('title', 'like', `${NUTRITION_PREFIX}%`);
    }

    await supabase.from('workout_plans').insert({
      user_id: user.id,
      title,
      title_ar,
      plan_data: planData,
      is_active: true,
    });
  };

  const buildCombinedUserProfile = async () => {
    // Use profile from React Context (always up-to-date)
    if (profile) {
      return {
        id: user?.id,
        user_id: user?.id,
        name: profile.name,
        age: profile.age,
        gender: profile.gender,
        weight: profile.weight,
        height: profile.height,
        goal: profile.goal,
        location: profile.location,
        fitnessLevel: profile.fitnessLevel,
        trainingDaysPerWeek: profile.trainingDaysPerWeek,
        equipment: profile.equipment || '',
        injuries: profile.injuries || '',
        activityLevel: profile.activityLevel,
        dietaryPreferences: profile.dietaryPreferences || '',
        chronicConditions: profile.chronicConditions || '',
        allergies: profile.allergies || '',
      };
    }

    if (!user) return null;

    // Fallback to Supabase if context profile not available
    const merged: Record<string, any> = {};

    try {
      const { data: profileData } = await supabase
        .from('profiles')
        .select('name,age,gender,weight,height,goal,location,fitness_level,training_days_per_week,equipment,injuries,activity_level,dietary_preferences,chronic_conditions,allergies')
        .eq('user_id', user.id)
        .maybeSingle();

      if (profileData) {
        merged.id = user.id;
        merged.user_id = user.id;
        merged.name = profileData.name;
        merged.age = profileData.age;
        merged.gender = profileData.gender;
        merged.weight = profileData.weight;
        merged.height = profileData.height;
        merged.goal = profileData.goal;
        merged.location = profileData.location;
        merged.fitnessLevel = (profileData as any).fitness_level;
        merged.trainingDaysPerWeek = (profileData as any).training_days_per_week;
        merged.equipment = (profileData as any).equipment || '';
        merged.injuries = (profileData as any).injuries || '';
        merged.activityLevel = (profileData as any).activity_level;
        merged.dietaryPreferences = (profileData as any).dietary_preferences || '';
        merged.chronicConditions = (profileData as any).chronic_conditions || '';
        merged.allergies = (profileData as any).allergies || '';
      }
    } catch (error) {
      console.error('Failed loading profiles table', error);
    }

    return Object.keys(merged).length > 0 ? merged : null;
  };

  const buildPlanSnapshot = async () => {
    if (!user) return null;

    try {
      const { data: activePlans } = await supabase
        .from('workout_plans')
        .select('title,is_active,updated_at')
        .eq('user_id', user.id)
        .eq('is_active', true);

      const workoutPlans = (activePlans || []).filter((plan) => !(plan.title || '').startsWith(NUTRITION_PREFIX));
      const nutritionPlans = (activePlans || []).filter((plan) => (plan.title || '').startsWith(NUTRITION_PREFIX));

      return {
        active_workout_plans: workoutPlans.length,
        active_nutrition_plans: nutritionPlans.length,
        workout_titles: workoutPlans.map((plan) => plan.title).filter(Boolean),
        nutrition_titles: nutritionPlans.map((plan) => plan.title).filter(Boolean),
        updated_at: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Failed building plan snapshot', error);
      return null;
    }
  };

  const buildTrackingSummary = async () => {
    if (!user) return null;

    try {
      const { data: plansData } = await supabase
        .from('workout_plans')
        .select('id,title,plan_data')
        .eq('user_id', user.id);

      const { data: completionsData } = await supabase
        .from('workout_completions')
        .select('id,completed_at')
        .eq('user_id', user.id);

      const { data: logsData } = await supabase
        .from('daily_logs')
        .select('log_date,workout_notes,nutrition_notes,mood')
        .eq('user_id', user.id);

      let totalTasks = 0;
      for (const plan of plansData || []) {
        const days = Array.isArray((plan as any).plan_data) ? (plan as any).plan_data : [];
        for (const day of days) {
          const exercises = Array.isArray(day?.exercises) ? day.exercises.length : 0;
          const meals = Array.isArray(day?.meals) ? day.meals.length : 0;
          totalTasks += exercises + meals;
        }
      }

      const completedTasks = (completionsData || []).length;
      const adherence = totalTasks > 0 ? Math.min(1, completedTasks / totalTasks) : 0;
      const activeWorkoutPlans = (plansData || []).filter((plan) => !(plan.title || '').startsWith(NUTRITION_PREFIX)).length;
      const activeNutritionPlans = (plansData || []).filter((plan) => (plan.title || '').startsWith(NUTRITION_PREFIX)).length;

      const sortedByDate = [...(completionsData || [])]
        .filter((row) => row.completed_at)
        .sort((a, b) => new Date(b.completed_at).getTime() - new Date(a.completed_at).getTime());
      const lastCompletionAt = sortedByDate[0]?.completed_at || null;
      const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
      const completedLast7Days = (completionsData || []).filter((row) => {
        if (!row.completed_at) return false;
        return new Date(row.completed_at).getTime() >= sevenDaysAgo;
      }).length;

      const dailyLogs = logsData || [];
      const logsLast7Days = dailyLogs.filter((row) => {
        if (!row.log_date) return false;
        return new Date(row.log_date).getTime() >= sevenDaysAgo;
      });
      const lastLogDate = dailyLogs
        .filter((row) => row.log_date)
        .sort((a, b) => new Date(b.log_date).getTime() - new Date(a.log_date).getTime())[0]?.log_date || null;

      return {
        completed_tasks: completedTasks,
        total_tasks: totalTasks,
        adherence_score: adherence,
        active_workout_plans: activeWorkoutPlans,
        active_nutrition_plans: activeNutritionPlans,
        completed_last_7_days: completedLast7Days,
        last_completed_at: lastCompletionAt,
        days_logged_last_7: logsLast7Days.length,
        last_log_date: lastLogDate,
      };
    } catch (error) {
      console.error('Failed building tracking summary', error);
      return null;
    }
  };

  const typeAssistantReply = useCallback(
    async (baseMessages: ChatMessage[], fullText: string): Promise<ChatMessage[]> => {
      const timestamp = Date.now();
      const seedMessage: ChatMessage = { role: 'assistant', content: '', timestamp };
      setCurrentMessages([...baseMessages, seedMessage]);

      if (!fullText) {
        return [...baseMessages, seedMessage];
      }

      setIsTypingReply(true);
      const charsPerTick =
        fullText.length > 1400 ? 20 : fullText.length > 900 ? 14 : fullText.length > 500 ? 9 : 5;
      const tickMs = 18;
      let cursor = 0;

      await new Promise<void>((resolve) => {
        const timer = window.setInterval(() => {
          cursor = Math.min(fullText.length, cursor + charsPerTick);
          const partialMessage: ChatMessage = {
            role: 'assistant',
            content: fullText.slice(0, cursor),
            timestamp,
          };
          setCurrentMessages([...baseMessages, partialMessage]);

          if (cursor >= fullText.length) {
            window.clearInterval(timer);
            resolve();
          }
        }, tickMs);
      });

      setIsTypingReply(false);
      return [...baseMessages, { role: 'assistant', content: fullText, timestamp }];
    },
    []
  );

  const sendMessageWithText = async (text: string) => {
    if (!text.trim() || isBusy || !user) return;

    const userMessage: ChatMessage = { role: 'user', content: text.trim(), timestamp: Date.now() };
    const newMessages = [...currentMessages, userMessage];
    setCurrentMessages(newMessages);
    setInput('');
    setIsLoading(true);

    if (currentId) {
      if (supabase && supabase.from) {
        try {
          await supabase.from('chat_messages').insert({
            conversation_id: currentId,
            user_id: user.id,
            role: 'user',
            content: text.trim(),
          });
          
          const conv = conversations.find(c => c.id === currentId);
          if (conv && !conv.title) {
            const title = text.trim().slice(0, 50) + (text.trim().length > 50 ? '...' : '');
            await supabase.from('chat_conversations').update({ title }).eq('id', currentId);
            setConversations(prev => prev.map(c => c.id === currentId ? { ...c, title } : c));
          }
        } catch (error) {
          console.warn('Failed to save message to Supabase:', error);
        }
      }
    }

    setConversations(prev => prev.map(c => 
      c.id === currentId ? { ...c, messages: newMessages, updated_at: new Date().toISOString() } : c
    ));
    try {
      const user_profile = await buildCombinedUserProfile();
      const tracking_summary = await buildTrackingSummary();
      const plan_snapshot = await buildPlanSnapshot();
      const recent_messages = newMessages.slice(-12).map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const payload = {
        message: text.trim(),
        user_id: user.id,
        conversation_id: currentId || user.id,
        language: language === 'ar' ? 'ar' : 'en',
        user_profile,
        tracking_summary,
        plan_snapshot,
        recent_messages,
      };

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 25000);
      const apiResponse = await fetch(`${AI_BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      window.clearTimeout(timeoutId);

      if (!apiResponse.ok) {
        throw new Error(`Backend error: ${apiResponse.status}`);
      }

      const data = await apiResponse.json();

      // prefer the textual reply from backend
      const assistantTextRaw = data?.reply || formatExercisesMessage(data?.exercises || []);
      const assistantText = repairMojibake(assistantTextRaw);
      const updatedMessages = await typeAssistantReply(newMessages, assistantText);
      setCurrentMessages(updatedMessages);
      setConversations(prev => prev.map(c =>
        c.id === currentId ? { ...c, messages: updatedMessages, updated_at: new Date().toISOString() } : c
      ));

      if (currentId) {
        await supabase.from('chat_messages').insert({
          conversation_id: currentId,
          user_id: user.id,
          role: 'assistant',
          content: assistantText,
        });
      }

      const pendingFromApi = extractPendingPlanFromResponse(data);
      if (pendingFromApi) {
        setPendingPlan(pendingFromApi);
      }

      try {
        await persistApprovedPlan(data);
        if (extractApprovedPlanFromResponse(data)) {
          setPendingPlan(null);
        }
      } catch (e) {
        console.error('Failed saving approved plan to Supabase', e);
      }

      if (autoSpeak) speakWithVoice(assistantText);
    } catch (error: any) {
      console.error('Error:', error);
      setIsTypingReply(false);
      const timeoutMessage = error?.name === 'AbortError'
        ? (language === 'ar'
          ? 'الرد تأخر. تأكد أن السيرفر شغال على المنفذ الصحيح ثم جرّب مرة ثانية.'
          : 'The response is taking too long. Make sure the backend is running on the correct port and try again.')
        : null;
      const errMsg: ChatMessage = {
        role: 'assistant',
        content:
          timeoutMessage ||
          (language === 'ar'
            ? `تعذر الاتصال بخادم الذكاء الاصطناعي (${AI_BACKEND_URL}). تأكد أنه يعمل ثم أعد المحاولة.`
            : `Could not reach the AI backend (${AI_BACKEND_URL}). Make sure it's running and try again.`),
        timestamp: Date.now(),
      };
      setCurrentMessages(prev => [...prev, errMsg]);
    } finally {
      setIsTypingReply(false);
      setIsLoading(false);
    }
  };

  const sendMessage = () => sendMessageWithText(input);

  const appendAssistantMessage = async (content: string) => {
    const aiMessage: ChatMessage = { role: 'assistant', content, timestamp: Date.now() };
    setCurrentMessages(prev => {
      const updatedMessages = [...prev, aiMessage];
      setConversations(conversationsPrev => conversationsPrev.map(c =>
        c.id === currentId ? { ...c, messages: updatedMessages, updated_at: new Date().toISOString() } : c
      ));
      return updatedMessages;
    });

    if (currentId && user) {
      await supabase.from('chat_messages').insert({
        conversation_id: currentId,
        user_id: user.id,
        role: 'assistant',
        content,
      });
    }
  };

  const handleApprovePlan = async (planId: string) => {
    if (!user) return;
    const response = await fetch(`${AI_BACKEND_URL}/plans/${planId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user.id,
        conversation_id: currentId || user.id,
      }),
    });

    if (!response.ok) {
      throw new Error(`Approve failed: ${response.status}`);
    }

    const data = await response.json();
    await persistApprovedPlan(data);
    setPendingPlan(null);

    const successText = language === 'ar'
      ? 'تم اعتماد الخطة وحفظها في صفحة الجدول.'
      : 'Plan approved and saved to your Schedule page.';
    await appendAssistantMessage(successText);
  };

  const handleRejectPlan = async (planId: string) => {
    if (!user) return;
    await fetch(`${AI_BACKEND_URL}/plans/${planId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user.id,
        conversation_id: currentId || user.id,
      }),
    });

    setPendingPlan(null);
    const rejectText = language === 'ar'
      ? 'تم رفض الخطة. اكتب لي التعديلات التي تريدها وسأعيد بناء خطة جديدة.'
      : 'Plan rejected. Tell me what to change and I will regenerate it.';
    await appendAssistantMessage(rejectText);
  };

  const workoutApprovalPlan = pendingPlan?.type === 'workout' ? {
    id: pendingPlan.id,
    name: pendingPlan.plan?.title || 'AI Workout Plan',
    duration_days: pendingPlan.plan?.duration_days || 7,
    exercises: (pendingPlan.plan?.days || [])
      .flatMap((day: any) => day?.exercises || [])
      .map((exercise: any) => exercise?.name)
      .filter(Boolean),
    status: 'pending' as const,
    created_at: pendingPlan.plan?.created_at || new Date().toISOString(),
  } : null;

  const nutritionApprovalPlan = pendingPlan?.type === 'nutrition' ? {
    id: pendingPlan.id,
    daily_calories: Number(pendingPlan.plan?.daily_calories || 0),
    meals: ((pendingPlan.plan?.days || [])[0]?.meals || []).map((meal: any) => ({
      name: meal?.name || 'Meal',
      macros: {
        protein: Number(meal?.protein || 0),
        carbs: Number(meal?.carbs || 0),
        fat: Number(meal?.fat || 0),
      },
    })),
    status: 'pending' as const,
    created_at: pendingPlan.plan?.created_at || new Date().toISOString(),
  } : null;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Enter') return;
    if (e.shiftKey) return;

    e.preventDefault();
    sendMessage();
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString(language === 'ar' ? 'ar' : 'en', { month: 'short', day: 'numeric' });
  };
  const cleanContent = (content: string) => content;

  const handleVoiceSelect = (voiceName: string) => {
    setSelectedVoice(voiceName);
    localStorage.setItem('fitcoach_voice', voiceName);
  };

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Bot className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">
              {language === 'ar' ? 'سجل دخولك للتحدث مع المدرب' : 'Sign in to chat with your AI Coach'}
            </p>
            <Button variant="hero" onClick={() => window.location.href = '/auth?force=1'}>
              {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <div className="flex-1 flex pt-16 pb-20 md:pb-0">
        {/* Sidebar - Desktop */}
        <aside className="hidden md:flex w-72 flex-col border-r border-border/50 bg-card/50">
          <div className="p-4">
            <Button variant="hero" className="w-full" onClick={createConversation}>
              <Plus className="w-4 h-4" />
              {t('coach.newChat')}
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin px-2">
            {conversations.map(conv => (
              <div
                key={conv.id}
                role="button"
                tabIndex={0}
                onClick={() => selectConversation(conv.id)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { selectConversation(conv.id); } }}
                className={`w-full text-left px-3 py-3 rounded-xl mb-1 flex items-center gap-3 transition-all group ${
                  conv.id === currentId ? 'bg-primary/10 text-primary' : 'hover:bg-secondary/50 text-muted-foreground'
                }`}
              >
                <MessageSquare className="w-4 h-4 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{conv.title || t('coach.newChat')}</p>
                  <p className="text-xs opacity-60">{formatDate(conv.updated_at)}</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-destructive transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </aside>

        {/* Mobile Sidebar Overlay */}
        <AnimatePresence>
          {sidebarOpen && (
            <>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
                onClick={() => setSidebarOpen(false)} />
              <motion.aside
                initial={{ x: language === 'ar' ? 300 : -300 }} animate={{ x: 0 }} exit={{ x: language === 'ar' ? 300 : -300 }}
                className="fixed top-16 bottom-0 w-72 bg-card border-r border-border/50 z-50 md:hidden flex flex-col"
                style={{ [language === 'ar' ? 'right' : 'left']: 0 }}
              >
                <div className="p-4 flex items-center justify-between">
                  <Button variant="hero" size="sm" onClick={createConversation} className="flex-1">
                    <Plus className="w-4 h-4" />
                    {t('coach.newChat')}
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)} className="ml-2">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex-1 overflow-y-auto px-2">
                  {conversations.map(conv => (
                    <button key={conv.id} onClick={() => selectConversation(conv.id)}
                      className={`w-full text-left px-3 py-3 rounded-xl mb-1 flex items-center gap-3 transition-all ${
                        conv.id === currentId ? 'bg-primary/10 text-primary' : 'hover:bg-secondary/50 text-muted-foreground'
                      }`}
                    >
                      <MessageSquare className="w-4 h-4 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{conv.title || t('coach.newChat')}</p>
                        <p className="text-xs opacity-60">{formatDate(conv.updated_at)}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4">
          <div className="flex items-center gap-3 py-3 border-b border-border/30">
            <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </Button>
            <div className="w-10 h-10 rounded-full bg-gradient-primary flex items-center justify-center shadow-glow">
              <Bot className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="flex-1">
              <h1 className="font-semibold text-foreground">{t('coach.title')}</h1>
              <p className="text-xs text-muted-foreground">{t('coach.subtitle')}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setShowVoiceSettings(!showVoiceSettings)}>
              <Settings2 className="w-4 h-4" />
            </Button>
            {isSupported && (
              <Button
                variant={voiceMode ? 'default' : 'ghost'}
                size="icon"
                onClick={toggleVoiceMode}
                title={language === 'ar' ? 'وضع محادثة صوتية' : 'Voice Conversation Mode'}
              >
                {voiceMode ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </Button>
            )}
            <Button
              variant={autoSpeak ? 'default' : 'ghost'} size="icon"
              onClick={() => { setAutoSpeak(!autoSpeak); if (isAssistantSpeaking) stopAllSpeech(); }}
            >
              {autoSpeak ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </Button>
          </div>

          {/* Voice Settings */}
          <AnimatePresence>
            {showVoiceSettings && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden border-b border-border/30"
              >
                <div className="p-3 flex items-center gap-3">
                  <span className="text-sm text-muted-foreground whitespace-nowrap">
                    {language === 'ar' ? 'صوت المدرب:' : 'Coach voice:'}
                  </span>
                  <Select value={selectedVoice || 'default'} onValueChange={handleVoiceSelect}>
                    <SelectTrigger className="flex-1 bg-secondary/50 border-0 h-9">
                      <SelectValue placeholder={language === 'ar' ? 'افتراضي' : 'Default'} />
                    </SelectTrigger>
                    <SelectContent className="max-h-60">
                      <SelectItem value="default">{language === 'ar' ? 'افتراضي' : 'Default'}</SelectItem>
                      {filteredVoices.length > 0 && (
                        <>
                          <div className="px-2 py-1 text-xs text-muted-foreground font-semibold">
                            {language === 'ar' ? 'أصوات عربية' : 'Matching Language'}
                          </div>
                          {filteredVoices.map((voice) => (
                            <SelectItem key={voice.name} value={voice.name}>
                              {voice.name} ({voice.lang})
                            </SelectItem>
                          ))}
                        </>
                      )}
                      {availableVoices.filter(v => !filteredVoices.includes(v)).length > 0 && (
                        <>
                          <div className="px-2 py-1 text-xs text-muted-foreground font-semibold">
                            {language === 'ar' ? 'أصوات أخرى' : 'Other Voices'}
                          </div>
                          {availableVoices.filter(v => !filteredVoices.includes(v)).map((voice) => (
                            <SelectItem key={voice.name} value={voice.name}>
                              {voice.name} ({voice.lang})
                            </SelectItem>
                          ))}
                        </>
                      )}
                    </SelectContent>
                  </Select>
                  <Button size="sm" variant="ghost" onClick={() => speakWithVoice(language === 'ar' ? 'مرحبًا، أنا مدربك الشخصي' : 'Hello, I am your personal coach')}>
                    <Volume2 className="w-4 h-4" />
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 py-4">
            {currentMessages.map((message, index) => (
              <motion.div key={`${currentId}-${index}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  message.role === 'user' ? 'bg-accent' : 'bg-gradient-primary'
                }`}>
                  {message.role === 'user' ? <User className="w-4 h-4 text-accent-foreground" /> : <Bot className="w-4 h-4 text-primary-foreground" />}
                </div>
                <div className="max-w-[80%] group relative">
                  <div className={`p-4 ${message.role === 'user' ? 'chat-bubble-user text-primary-foreground' : 'chat-bubble-ai text-foreground'}`}>
                    {message.role === 'assistant' ? (
                      <div className="prose prose-sm prose-invert max-w-none">
                        <ReactMarkdown>{cleanContent(message.content)}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                  {message.role === 'assistant' && (
                    <button onClick={() => isAssistantSpeaking ? stopAllSpeech() : speakWithVoice(message.content)}
                      className="absolute -bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-card border border-border rounded-full p-1.5 hover:bg-secondary"
                    >
                      {isAssistantSpeaking ? <VolumeX className="w-3 h-3 text-muted-foreground" /> : <Volume2 className="w-3 h-3 text-muted-foreground" />}
                    </button>
                  )}
                </div>
              </motion.div>
            ))}
            {isLoading && !isTypingReply && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary-foreground" />
                </div>
                <div className="chat-bubble-ai p-4">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-sm text-muted-foreground">{language === 'ar' ? 'جاري التفكير...' : 'Thinking...'}</span>
                  </div>
                </div>
              </motion.div>
            )}
            {isVoiceProcessing && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary-foreground" />
                </div>
                <div className="chat-bubble-ai p-4">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                    <span className="text-sm text-muted-foreground">
                      {language === 'ar' ? 'جاري معالجة الصوت...' : 'Processing voice...'}
                    </span>
                  </div>
                </div>
              </motion.div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {workoutApprovalPlan && (
            <div className="mb-4">
              <PlanApprovalUI
                type="workout"
                plan={workoutApprovalPlan}
                onApprove={handleApprovePlan}
                onReject={handleRejectPlan}
              />
            </div>
          )}

          {nutritionApprovalPlan && (
            <div className="mb-4">
              <PlanApprovalUI
                type="nutrition"
                plan={nutritionApprovalPlan}
                onApprove={handleApprovePlan}
                onReject={handleRejectPlan}
              />
            </div>
          )}

          {/* Voice Indicator */}
          <AnimatePresence>
            {isListening && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
                className="flex items-center justify-center gap-3 py-3"
              >
                <div className="flex items-center gap-2 bg-destructive/10 text-destructive px-4 py-2 rounded-full">
                  <div className="w-3 h-3 bg-destructive rounded-full animate-pulse" />
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'جاري الاستماع... اضغط المايك للإرسال' : 'Listening... tap mic again to send'}
                  </span>
                  <button onClick={stopListening} className="ml-2"><MicOff className="w-4 h-4" /></button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {isAssistantSpeaking && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }}
                className="flex items-center justify-center gap-3 py-1"
              >
                <div className="flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full">
                  <Volume2 className="w-4 h-4 animate-pulse" />
                  <span className="text-sm font-medium">
                    {language === 'ar' ? 'المدرب يتحدث...' : 'Coach is speaking...'}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {voiceError && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }}
                className="flex items-center justify-center py-1"
              >
                <button
                  type="button"
                  onClick={clearError}
                  className="text-xs text-destructive/90 bg-destructive/10 border border-destructive/30 rounded-full px-3 py-1"
                >
                  {voiceError}
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input */}
          <div className="glass-card rounded-2xl p-3 mb-4">
            <div className="flex gap-2 items-end">
              {isSupported && (
                <Button variant={isListening ? 'destructive' : 'ghost'} size="icon"
                  onClick={isListening ? stopListening : startListeningIfPossible}
                  disabled={isBusy || isAssistantSpeaking}
                  className={`shrink-0 ${isListening ? 'animate-pulse' : ''}`}
                >
                  {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
              )}
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  language === 'ar'
                    ? 'اكتب رسالتك...'
                    : 'Type your message...'
                }
                className="bg-secondary/50 border-0 focus-visible:ring-1 min-h-[52px] max-h-40 resize-y"
                disabled={isBusy}
                rows={2}
              />
              <Button variant="hero" size="icon" onClick={sendMessage} disabled={isBusy || !input.trim()} className="shrink-0">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
