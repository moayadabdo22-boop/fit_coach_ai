import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface UserProfile {
  name: string;
  age: number;
  gender: 'male' | 'female';
  weight: number;
  height: number;
  goal: 'bulking' | 'cutting' | 'fitness';
  location: 'home' | 'gym';
  chronicConditions?: string;
  allergies?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ProgressData {
  totalExercises: number;
  completedExercises: number;
  totalMeals: number;
  completedMeals: number;
  activePlanTitle: string;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { messages, userProfile, language, progressData } = await req.json() as {
      messages: Message[];
      userProfile: UserProfile | null;
      language: 'en' | 'ar';
      progressData?: ProgressData | null;
    };

    const AI_GATEWAY_URL = Deno.env.get("AI_GATEWAY_URL") ?? "http://127.0.0.1:11434/v1/chat/completions";
    const AI_MODEL = Deno.env.get("AI_MODEL") ?? "llama3.1:8b";
    const AI_API_KEY = Deno.env.get("AI_API_KEY") ?? "";

    const healthInfo = userProfile
      ? [
          userProfile.chronicConditions ? `- Chronic Conditions: ${userProfile.chronicConditions}` : null,
          userProfile.allergies ? `- Allergies: ${userProfile.allergies}` : null,
        ].filter(Boolean).join('\n') || '- No chronic conditions or allergies reported'
      : '- No health information available';

    const userContext = userProfile
      ? `
User Profile:
- Name: ${userProfile.name} (IMPORTANT: When greeting or referring to the user, use their exact name "${userProfile.name}" as-is. Do NOT transliterate or change the spelling. Say the name exactly as written.)
- Age: ${userProfile.age} years old
- Gender: ${userProfile.gender}
- Weight: ${userProfile.weight} kg
- Height: ${userProfile.height} cm
- BMI: ${(userProfile.weight / Math.pow(userProfile.height / 100, 2)).toFixed(1)}
- Fitness Goal: ${userProfile.goal === 'bulking' ? 'Build Muscle' : userProfile.goal === 'cutting' ? 'Lose Weight' : 'General Fitness'}
- Workout Location: ${userProfile.location === 'home' ? 'Home (no gym equipment)' : 'Gym (full equipment access)'}
${healthInfo}
`
      : 'No user profile available yet.';

    const progressContext = progressData
      ? `
User's Current Progress:
- Active Plan: ${progressData.activePlanTitle}
- Exercises: ${progressData.completedExercises}/${progressData.totalExercises} completed
- Meals: ${progressData.completedMeals}/${progressData.totalMeals} completed
- Overall: ${progressData.totalExercises + progressData.totalMeals > 0 ? Math.round(((progressData.completedExercises + progressData.completedMeals) / (progressData.totalExercises + progressData.totalMeals)) * 100) : 0}% done
`
      : '';

    const systemPrompt = `You are FitCoach AI, a professional and friendly fitness coach and nutritionist.

${userContext}
${progressContext}

CRITICAL RULES:
1. You MUST ONLY discuss fitness, workouts, exercises, nutrition, health, and wellness topics.
2. If the user asks about ANY non-fitness topic, redirect: "${language === 'ar' ? 'أنا مدربك الرياضي! خليني أساعدك بالتمارين والتغذية 💪' : "I'm your fitness coach! Let me help you with workouts and nutrition 💪"}"
3. NEVER discuss non-fitness topics even if the user insists.
4. KEEP RESPONSES SHORT AND CONCISE - max 2-3 sentences unless the user asks for details or a plan.
5. DO NOT proactively give a full plan. Ask what they need first.
6. Only provide a detailed plan when SPECIFICALLY asked (e.g., "give me a plan", "أعطيني جدول").

LANGUAGE RULES:
- Current language: ${language === 'ar' ? 'Arabic' : 'English'}
- If language is Arabic: respond ONLY in Arabic. Use Jordanian/Palestinian dialect. DO NOT mix English words.
- If language is English: respond ONLY in English. DO NOT mix Arabic words.
- User's name should always be written exactly as stored: "${userProfile?.name || ''}"

HEALTH CONDITIONS:
${userProfile?.chronicConditions ? `The user has: ${userProfile.chronicConditions}. ALWAYS consider these when recommending exercises and nutrition. Avoid exercises or foods that could aggravate these conditions. Warn about risks.` : 'If the user hasn\'t mentioned health conditions, ask once: "' + (language === 'ar' ? 'عندك أي أمراض مزمنة لازم أعرف عنها؟' : 'Do you have any chronic conditions I should know about?') + '"'}

PROGRESS TRACKING:
${progressData ? `You can see the user's progress. When they ask about their progress, give them encouragement and specific feedback based on their completion rates. ${language === 'ar' ? 'شجّع المستخدم وأعطيه ملاحظات محددة.' : 'Encourage the user and give specific feedback.'}` : ''}

WEBSITE NAVIGATION:
- ${language === 'ar' ? 'تمارين/فيديوهات/تكنيك ← "روح لصفحة **التمارين** (/workouts) فيها فيديوهات لكل تمرين!"' : 'Exercises/videos/technique → "Check the **Workouts** page (/workouts) for exercise videos filtered by muscle group!"'}
- ${language === 'ar' ? 'الملف/الإحصائيات ← صفحة **الملف** (/profile)' : 'Profile/stats → **Profile** page (/profile)'}
- ${language === 'ar' ? 'الجدول/المتابعة ← صفحة **الجدول** (/schedule)' : 'Schedule/tracking → **Schedule** page (/schedule)'}

WORKOUT PLAN FORMAT (only when asked):
When generating a workout plan, ask the user:
1. How many days per week? Which days are rest days?
2. Any injuries or limitations?

Then generate using WEEKDAY names in this EXACT format:
\`\`\`workout_plan
{
  "title": "Plan Title",
  "title_ar": "عنوان الخطة",
  "days": [
    {
      "day": "Saturday - Chest & Triceps",
      "dayAr": "السبت - صدر وتراي",
      "exercises": [
        {"name": "Bench Press", "nameAr": "بنش برس", "sets": "4", "reps": "8-10"}
      ]
    }
  ]
}
\`\`\`
Use actual weekday names (Saturday, Sunday, Monday...). Include rest days as {"day": "Tuesday - Rest Day", "dayAr": "الثلاثاء - راحة", "exercises": []}.

NUTRITION PLAN FORMAT (only when asked):
When generating a nutrition/meal plan, generate using this EXACT format:
\`\`\`nutrition_plan
{
  "title": "Nutrition Plan",
  "title_ar": "النظام الغذائي",
  "days": [
    {
      "day": "Saturday",
      "dayAr": "السبت",
      "meals": [
        {"name": "Breakfast", "nameAr": "فطور", "description": "3 eggs + oats + banana", "descriptionAr": "٣ بيضات + شوفان + موزة", "calories": "450"},
        {"name": "Lunch", "nameAr": "غداء", "description": "Grilled chicken + rice + salad", "descriptionAr": "دجاج مشوي + رز + سلطة", "calories": "650"}
      ]
    }
  ]
}
\`\`\`
${userProfile?.chronicConditions ? `IMPORTANT: Avoid foods that conflict with: ${userProfile.chronicConditions}. For diabetes: avoid high-sugar foods. For blood pressure: limit sodium.` : ''}
After the plan, ask: "${language === 'ar' ? 'بدك تعتمد هالجدول؟' : 'Would you like to adopt this plan?'}"

Guidelines:
1. Consider goal, gender, age, location, and HEALTH CONDITIONS
2. Home = bodyweight only. Gym = full equipment.
3. Be specific with sets/reps/rest when discussing exercises
4. For nutrition: calculate calories based on user stats and goal
5. Prioritize safety - proper form, warm up
6. Adapt for age and gender
7. Keep answers brief unless asked for detail`;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (AI_API_KEY) {
      headers.Authorization = `Bearer ${AI_API_KEY}`;
    }

    const response = await fetch(AI_GATEWAY_URL, {
      method: "POST",
      headers,
      body: JSON.stringify({
        model: AI_MODEL,
        messages: [
          { role: "system", content: systemPrompt },
          ...messages.map((m: Message) => ({ role: m.role, content: m.content })),
        ],
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        return new Response(
          JSON.stringify({ error: language === 'ar' ? 'انتظر شوي وجرب مرة ثانية.' : 'Rate limit exceeded. Please try again in a moment.' }),
          { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
      if (response.status === 402) {
        return new Response(
          JSON.stringify({ error: language === 'ar' ? 'الخدمة مش متاحة حالياً. جرب بعدين.' : 'Service temporarily unavailable. Please try again later.' }),
          { status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
      const errorText = await response.text();
      console.error("AI gateway error:", response.status, errorText);
      throw new Error("AI gateway error");
    }

    const data = await response.json();
    const assistantMessage = data.choices?.[0]?.message?.content;

    if (!assistantMessage) {
      throw new Error("No response from AI");
    }

    return new Response(
      JSON.stringify({ response: assistantMessage }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("AI Coach error:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Unknown error"
      }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
