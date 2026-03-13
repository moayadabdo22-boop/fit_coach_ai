import { repairMojibake } from '@/lib/text';

export interface Exercise {
  id: string;
  name: string;
  nameAr: string;
  muscle: string;
  goal: 'bulking' | 'cutting' | 'fitness' | 'all';
  location: 'home' | 'gym' | 'both';
  gender: 'male' | 'female' | 'all';
  sets: number;
  reps: string;
  videoUrl: string;
  description: string;
  descriptionAr: string;
}

const rawExercises: Exercise[] = [
  // ===== CHEST =====
  { id: 'push-ups', name: 'Push-Ups', nameAr: 'ØªÙ…Ø±ÙŠÙ† Ø§Ù„Ø¶ØºØ·', muscle: 'chest', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Classic bodyweight exercise targeting chest, shoulders, and triceps.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† ÙƒÙ„Ø§Ø³ÙŠÙƒÙŠ Ø¨ÙˆØ²Ù† Ø§Ù„Ø¬Ø³Ù… ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„ØµØ¯Ø± ÙˆØ§Ù„Ø£ÙƒØªØ§Ù ÙˆØ§Ù„ØªØ±Ø§ÙŠ.' },
  { id: 'bench-press', name: 'Bench Press', nameAr: 'Ø¶ØºØ· Ø§Ù„Ø¨Ù†Ø´', muscle: 'chest', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '8-10', videoUrl: '', description: 'Compound exercise for building chest mass and strength.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ù…Ø±ÙƒØ¨ Ù„Ø¨Ù†Ø§Ø¡ ÙƒØªÙ„Ø© Ø§Ù„ØµØ¯Ø± ÙˆÙ‚ÙˆØªÙ‡.' },
  { id: 'incline-push-ups', name: 'Incline Push-Ups', nameAr: 'Ø¶ØºØ· Ù…Ø§Ø¦Ù„', muscle: 'chest', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '15-20', videoUrl: '', description: 'Beginner-friendly push-up variation using an elevated surface.', descriptionAr: 'Ù†Ø³Ø®Ø© Ø³Ù‡Ù„Ø© Ù…Ù† ØªÙ…Ø±ÙŠÙ† Ø§Ù„Ø¶ØºØ· Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø³Ø·Ø­ Ù…Ø±ØªÙØ¹.' },
  { id: 'incline-bench-press', name: 'Incline Bench Press', nameAr: 'Ø¶ØºØ· Ø¨Ù†Ø´ Ù…Ø§Ø¦Ù„', muscle: 'chest', goal: 'bulking', location: 'gym', gender: 'male', sets: 4, reps: '8-10', videoUrl: '', description: 'Targets upper chest for a fuller, more balanced chest development.', descriptionAr: 'ÙŠØ³ØªÙ‡Ø¯Ù Ø£Ø¹Ù„Ù‰ Ø§Ù„ØµØ¯Ø± Ù„ØªØ·ÙˆÙŠØ± Ø£ÙƒØ«Ø± ØªÙˆØ§Ø²Ù†Ø§Ù‹.' },
  { id: 'chest-fly', name: 'Chest Fly', nameAr: 'ÙÙ„Ø§ÙŠ Ø§Ù„ØµØ¯Ø±', muscle: 'chest', goal: 'all', location: 'gym', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Isolation exercise that stretches and contracts the chest muscles.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¹Ø²Ù„ ÙŠÙ…Ø¯Ø¯ ÙˆÙŠÙ‚Ø¨Ø¶ Ø¹Ø¶Ù„Ø§Øª Ø§Ù„ØµØ¯Ø±.' },
  { id: 'knee-push-ups', name: 'Knee Push-Ups', nameAr: 'Ø¶ØºØ· Ø¹Ù„Ù‰ Ø§Ù„Ø±ÙƒØ¨', muscle: 'chest', goal: 'fitness', location: 'home', gender: 'female', sets: 3, reps: '12-15', videoUrl: '', description: 'Modified push-ups for beginners, great for building upper body strength.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¶ØºØ· Ù…Ø¹Ø¯Ù‘Ù„ Ù„Ù„Ù…Ø¨ØªØ¯Ø¦ÙŠÙ†ØŒ Ù…Ù…ØªØ§Ø² Ù„Ø¨Ù†Ø§Ø¡ Ù‚ÙˆØ© Ø§Ù„Ø¬Ø²Ø¡ Ø§Ù„Ø¹Ù„ÙˆÙŠ.' },
  { id: 'chest-press-machine', name: 'Chest Press Machine', nameAr: 'Ø¢Ù„Ø© Ø¶ØºØ· Ø§Ù„ØµØ¯Ø±', muscle: 'chest', goal: 'fitness', location: 'gym', gender: 'female', sets: 3, reps: '12-15', videoUrl: '', description: 'Machine-guided chest press for controlled movement and toning.', descriptionAr: 'Ø¶ØºØ· ØµØ¯Ø± Ø¨Ø§Ù„Ø¢Ù„Ø© Ù„Ø­Ø±ÙƒØ© Ù…Ø¶Ø¨ÙˆØ·Ø© ÙˆØªÙ†Ø³ÙŠÙ‚.' },
  { id: 'decline-bench-press', name: 'Decline Bench Press', nameAr: 'Ø¨Ù†Ø´ Ù‡Ø§Ø¨Ø·', muscle: 'chest', goal: 'bulking', location: 'gym', gender: 'male', sets: 4, reps: '8-10', videoUrl: '', description: 'Targets lower chest for complete chest development.', descriptionAr: 'ÙŠØ³ØªÙ‡Ø¯Ù Ø£Ø³ÙÙ„ Ø§Ù„ØµØ¯Ø± Ù„ØªØ·ÙˆÙŠØ± ÙƒØ§Ù…Ù„.' },

  // ===== BACK =====
  { id: 'pull-ups', name: 'Pull-Ups', nameAr: 'Ø§Ù„Ø¹Ù‚Ù„Ø©', muscle: 'back', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '8-12', videoUrl: '', description: 'Excellent compound exercise for back and biceps development.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ù…Ø±ÙƒØ¨ Ù…Ù…ØªØ§Ø² Ù„ØªØ·ÙˆÙŠØ± Ø§Ù„Ø¸Ù‡Ø± ÙˆØ§Ù„Ø¨Ø§ÙŠ.' },
  { id: 'bent-over-rows', name: 'Bent Over Rows', nameAr: 'Ø§Ù„ØªØ¬Ø¯ÙŠÙ Ø§Ù„Ù…Ø§Ø¦Ù„', muscle: 'back', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '8-10', videoUrl: '', description: 'Heavy compound movement for building a thick back.', descriptionAr: 'Ø­Ø±ÙƒØ© Ù…Ø±ÙƒØ¨Ø© Ø«Ù‚ÙŠÙ„Ø© Ù„Ø¨Ù†Ø§Ø¡ Ø¸Ù‡Ø± Ø³Ù…ÙŠÙƒ.' },
  { id: 'superman', name: 'Superman Hold', nameAr: 'ØªÙ…Ø±ÙŠÙ† Ø³ÙˆØ¨Ø±Ù…Ø§Ù†', muscle: 'back', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '30 sec', videoUrl: '', description: 'Bodyweight exercise for lower back strength.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨ÙˆØ²Ù† Ø§Ù„Ø¬Ø³Ù… Ù„Ù‚ÙˆØ© Ø£Ø³ÙÙ„ Ø§Ù„Ø¸Ù‡Ø±.' },
  { id: 'lat-pulldown', name: 'Lat Pulldown', nameAr: 'Ø³Ø­Ø¨ Ø¹Ø§Ù„ÙŠ', muscle: 'back', goal: 'all', location: 'gym', gender: 'all', sets: 4, reps: '10-12', videoUrl: '', description: 'Machine exercise targeting lats for a wider back.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¢Ù„Ø© ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„Ù„Ø§ØªØ³ Ù„Ø¸Ù‡Ø± Ø£Ø¹Ø±Ø¶.' },
  { id: 'seated-cable-row', name: 'Seated Cable Row', nameAr: 'ØªØ¬Ø¯ÙŠÙ Ø¬Ø§Ù„Ø³ Ø¨Ø§Ù„ÙƒÙŠØ¨Ù„', muscle: 'back', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '10-12', videoUrl: '', description: 'Cable exercise for overall back thickness.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† ÙƒÙŠØ¨Ù„ Ù„Ø³Ù…Ø§ÙƒØ© Ø§Ù„Ø¸Ù‡Ø±.' },
  { id: 'resistance-band-rows', name: 'Resistance Band Rows', nameAr: 'ØªØ¬Ø¯ÙŠÙ Ø¨Ø§Ù„Ø­Ø¨Ù„ Ø§Ù„Ù…Ø·Ø§Ø·ÙŠ', muscle: 'back', goal: 'fitness', location: 'home', gender: 'female', sets: 3, reps: '15-20', videoUrl: '', description: 'Light resistance exercise for toning the back.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨Ù…Ù‚Ø§ÙˆÙ…Ø© Ø®ÙÙŠÙØ© Ù„ØªÙ†Ø³ÙŠÙ‚ Ø§Ù„Ø¸Ù‡Ø±.' },
  { id: 'single-arm-row', name: 'Single Arm Dumbbell Row', nameAr: 'ØªØ¬Ø¯ÙŠÙ Ø°Ø±Ø§Ø¹ ÙˆØ§Ø­Ø¯Ø©', muscle: 'back', goal: 'all', location: 'gym', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Unilateral back exercise for balanced development.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¸Ù‡Ø± Ø£Ø­Ø§Ø¯ÙŠ Ù„ØªØ·ÙˆÙŠØ± Ù…ØªÙˆØ§Ø²Ù†.' },

  // ===== SHOULDERS =====
  { id: 'shoulder-press', name: 'Shoulder Press', nameAr: 'Ø¶ØºØ· Ø§Ù„ÙƒØªÙ', muscle: 'shoulders', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '8-10', videoUrl: '', description: 'Overhead press for building shoulder mass.', descriptionAr: 'Ø¶ØºØ· Ø¹Ù„ÙˆÙŠ Ù„Ø¨Ù†Ø§Ø¡ ÙƒØªÙ„Ø© Ø§Ù„ÙƒØªÙ.' },
  { id: 'pike-push-ups', name: 'Pike Push-Ups', nameAr: 'Ø¶ØºØ· Ø§Ù„Ø±Ù…Ø­', muscle: 'shoulders', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Bodyweight shoulder exercise mimicking overhead press.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† ÙƒØªÙ Ø¨ÙˆØ²Ù† Ø§Ù„Ø¬Ø³Ù… ÙŠØ­Ø§ÙƒÙŠ Ø§Ù„Ø¶ØºØ· Ø§Ù„Ø¹Ù„ÙˆÙŠ.' },
  { id: 'lateral-raises', name: 'Lateral Raises', nameAr: 'Ø±ÙØ¹ Ø¬Ø§Ù†Ø¨ÙŠ', muscle: 'shoulders', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Isolation exercise for side deltoids.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¹Ø²Ù„ Ù„Ù„Ø¯Ø§Ù„ÙŠØ© Ø§Ù„Ø¬Ø§Ù†Ø¨ÙŠØ©.' },
  { id: 'front-raises', name: 'Front Raises', nameAr: 'Ø±ÙØ¹ Ø£Ù…Ø§Ù…ÙŠ', muscle: 'shoulders', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Targets the front deltoids for balanced shoulder development.', descriptionAr: 'ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„Ø¯Ø§Ù„ÙŠØ© Ø§Ù„Ø£Ù…Ø§Ù…ÙŠØ© Ù„ØªØ·ÙˆÙŠØ± Ù…ØªÙˆØ§Ø²Ù† Ù„Ù„ÙƒØªÙ.' },
  { id: 'face-pulls', name: 'Face Pulls', nameAr: 'Ø³Ø­Ø¨ Ø§Ù„ÙˆØ¬Ù‡', muscle: 'shoulders', goal: 'fitness', location: 'gym', gender: 'all', sets: 3, reps: '15-20', videoUrl: '', description: 'Excellent for rear delts and rotator cuff health.', descriptionAr: 'Ù…Ù…ØªØ§Ø² Ù„Ù„Ø¯Ø§Ù„ÙŠØ© Ø§Ù„Ø®Ù„ÙÙŠØ© ÙˆØµØ­Ø© Ø§Ù„ÙƒØªÙ.' },
  { id: 'light-lateral-raises', name: 'Light Lateral Raises', nameAr: 'Ø±ÙØ¹ Ø¬Ø§Ù†Ø¨ÙŠ Ø®ÙÙŠÙ', muscle: 'shoulders', goal: 'cutting', location: 'both', gender: 'female', sets: 3, reps: '15-20', videoUrl: '', description: 'Light lateral raises for toning shoulders.', descriptionAr: 'Ø±ÙØ¹ Ø¬Ø§Ù†Ø¨ÙŠ Ø®ÙÙŠÙ Ù„ØªÙ†Ø³ÙŠÙ‚ Ø§Ù„Ø£ÙƒØªØ§Ù.' },

  // ===== BICEPS =====
  { id: 'bicep-curls', name: 'Bicep Curls', nameAr: 'ÙƒÙŠØ±Ù„ Ø§Ù„Ø¨Ø§ÙŠ', muscle: 'biceps', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Classic isolation exercise for biceps.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¹Ø²Ù„ ÙƒÙ„Ø§Ø³ÙŠÙƒÙŠ Ù„Ù„Ø¨Ø§ÙŠ.' },
  { id: 'chin-ups', name: 'Chin-Ups', nameAr: 'Ø³Ø­Ø¨ Ø¨Ù‚Ø¨Ø¶Ø© Ù…Ø¹ÙƒÙˆØ³Ø©', muscle: 'biceps', goal: 'bulking', location: 'both', gender: 'all', sets: 3, reps: '8-10', videoUrl: '', description: 'Compound exercise emphasizing biceps with back involvement.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ù…Ø±ÙƒØ¨ ÙŠØ±ÙƒØ² Ø¹Ù„Ù‰ Ø§Ù„Ø¨Ø§ÙŠ Ù…Ø¹ Ø¥Ø´Ø±Ø§Ùƒ Ø§Ù„Ø¸Ù‡Ø±.' },
  { id: 'hammer-curls', name: 'Hammer Curls', nameAr: 'ÙƒÙŠØ±Ù„ Ø§Ù„Ù…Ø·Ø±Ù‚Ø©', muscle: 'biceps', goal: 'bulking', location: 'both', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Targets brachialis and forearms along with biceps.', descriptionAr: 'ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„Ø¹Ø¶Ù„Ø© Ø§Ù„Ø¹Ø¶Ø¯ÙŠØ© ÙˆØ§Ù„Ø³Ø§Ø¹Ø¯ Ù…Ø¹ Ø§Ù„Ø¨Ø§ÙŠ.' },
  { id: 'concentration-curls', name: 'Concentration Curls', nameAr: 'ÙƒÙŠØ±Ù„ Ø§Ù„ØªØ±ÙƒÙŠØ²', muscle: 'biceps', goal: 'cutting', location: 'both', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Isolated bicep exercise for peak contraction.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¹Ø²Ù„ Ù„Ù„Ø¨Ø§ÙŠ Ù„Ø£Ù‚ØµÙ‰ Ø§Ù†Ù‚Ø¨Ø§Ø¶.' },
  { id: 'light-bicep-curls', name: 'Light Dumbbell Curls', nameAr: 'ÙƒÙŠØ±Ù„ Ø®ÙÙŠÙ', muscle: 'biceps', goal: 'fitness', location: 'both', gender: 'female', sets: 3, reps: '15-20', videoUrl: '', description: 'Light curls for toning arms without bulking.', descriptionAr: 'ÙƒÙŠØ±Ù„ Ø®ÙÙŠÙ Ù„ØªÙ†Ø³ÙŠÙ‚ Ø§Ù„Ø°Ø±Ø§Ø¹ÙŠÙ† Ø¨Ø¯ÙˆÙ† ØªØ¶Ø®ÙŠÙ….' },

  // ===== TRICEPS =====
  { id: 'tricep-dips', name: 'Tricep Dips', nameAr: 'Ø§Ù†Ø®ÙØ§Ø¶Ø§Øª Ø§Ù„ØªØ±Ø§ÙŠ', muscle: 'triceps', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Bodyweight exercise for triceps using a bench or chair.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨ÙˆØ²Ù† Ø§Ù„Ø¬Ø³Ù… Ù„Ù„ØªØ±Ø§ÙŠ Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… Ù…Ù‚Ø¹Ø¯ Ø£Ùˆ ÙƒØ±Ø³ÙŠ.' },
  { id: 'diamond-push-ups', name: 'Diamond Push-Ups', nameAr: 'Ø¶ØºØ· Ø§Ù„Ù…Ø§Ø³Ø©', muscle: 'triceps', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Push-up variation targeting triceps with hands close together.', descriptionAr: 'Ù†Ø³Ø®Ø© Ù…Ù† ØªÙ…Ø±ÙŠÙ† Ø§Ù„Ø¶ØºØ· ØªØ³ØªÙ‡Ø¯Ù Ø§Ù„ØªØ±Ø§ÙŠ Ø¨Ø§Ù„Ø£ÙŠØ¯ÙŠ Ù…ØªÙ‚Ø§Ø±Ø¨Ø©.' },
  { id: 'tricep-pushdown', name: 'Tricep Pushdown', nameAr: 'Ø¯ÙØ¹ ØªØ±Ø§ÙŠ Ø¨Ø§Ù„ÙƒÙŠØ¨Ù„', muscle: 'triceps', goal: 'all', location: 'gym', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Cable exercise isolating the triceps effectively.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† ÙƒÙŠØ¨Ù„ Ù„Ø¹Ø²Ù„ Ø§Ù„ØªØ±Ø§ÙŠ Ø¨ÙØ¹Ø§Ù„ÙŠØ©.' },
  { id: 'overhead-tricep-extension', name: 'Overhead Tricep Extension', nameAr: 'ØªÙ…Ø¯ÙŠØ¯ Ø§Ù„ØªØ±Ø§ÙŠ Ø§Ù„Ø¹Ù„ÙˆÙŠ', muscle: 'triceps', goal: 'bulking', location: 'both', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Stretches and targets the long head of the triceps.', descriptionAr: 'ÙŠÙ…Ø¯Ø¯ ÙˆÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„Ø±Ø£Ø³ Ø§Ù„Ø·ÙˆÙŠÙ„ Ù„Ù„ØªØ±Ø§ÙŠ.' },
  { id: 'tricep-kickback', name: 'Tricep Kickback', nameAr: 'Ø±ÙƒÙ„Ø© ØªØ±Ø§ÙŠ Ø®Ù„ÙÙŠØ©', muscle: 'triceps', goal: 'cutting', location: 'both', gender: 'female', sets: 3, reps: '12-15', videoUrl: '', description: 'Isolation exercise for toning the back of the arms.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¹Ø²Ù„ Ù„ØªÙ†Ø³ÙŠÙ‚ Ø®Ù„Ù Ø§Ù„Ø°Ø±Ø§Ø¹.' },

  // ===== ABS =====
  { id: 'plank', name: 'Plank', nameAr: 'Ø§Ù„Ø¨Ù„Ø§Ù†Ùƒ', muscle: 'abs', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '30-60 sec', videoUrl: '', description: 'Isometric core exercise for overall stability.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ù…ØªØ³Ø§ÙˆÙŠ Ø§Ù„Ù‚ÙŠØ§Ø³ Ù„Ù„Ø¬Ø°Ø¹ Ù„Ù„Ø«Ø¨Ø§Øª Ø§Ù„Ø¹Ø§Ù….' },
  { id: 'crunches', name: 'Crunches', nameAr: 'Ø§Ù„ÙƒØ±Ø§Ù†Ø´', muscle: 'abs', goal: 'cutting', location: 'home', gender: 'all', sets: 3, reps: '15-20', videoUrl: '', description: 'Classic ab exercise targeting rectus abdominis.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨Ø·Ù† ÙƒÙ„Ø§Ø³ÙŠÙƒÙŠ ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„Ø¹Ø¶Ù„Ø© Ø§Ù„Ù…Ø³ØªÙ‚ÙŠÙ…Ø© Ø§Ù„Ø¨Ø·Ù†ÙŠØ©.' },
  { id: 'leg-raises', name: 'Leg Raises', nameAr: 'Ø±ÙØ¹ Ø§Ù„Ø£Ø±Ø¬Ù„', muscle: 'abs', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Lower ab exercise hanging or lying down.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø£Ø³ÙÙ„ Ø§Ù„Ø¨Ø·Ù† Ù…Ø¹Ù„Ù‚Ø§Ù‹ Ø£Ùˆ Ù…Ø³ØªÙ„Ù‚ÙŠØ§Ù‹.' },
  { id: 'mountain-climbers', name: 'Mountain Climbers', nameAr: 'ØªØ³Ù„Ù‚ Ø§Ù„Ø¬Ø¨Ù„', muscle: 'abs', goal: 'cutting', location: 'home', gender: 'all', sets: 3, reps: '30 sec', videoUrl: '', description: 'Dynamic core and cardio exercise for fat burning.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¯ÙŠÙ†Ø§Ù…ÙŠÙƒÙŠ Ù„Ù„Ø¬Ø°Ø¹ ÙˆØ§Ù„Ù‚Ù„Ø¨ Ù„Ø­Ø±Ù‚ Ø§Ù„Ø¯Ù‡ÙˆÙ†.' },
  { id: 'russian-twists', name: 'Russian Twists', nameAr: 'Ø§Ù„Ù„Ù Ø§Ù„Ø±ÙˆØ³ÙŠ', muscle: 'abs', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '20 each', videoUrl: '', description: 'Rotational exercise targeting obliques and core.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¯ÙˆØ±Ø§Ù†ÙŠ ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„Ø¹Ø¶Ù„Ø§Øª Ø§Ù„Ù…Ø§Ø¦Ù„Ø© ÙˆØ§Ù„Ø¬Ø°Ø¹.' },
  { id: 'cable-crunches', name: 'Cable Crunches', nameAr: 'ÙƒØ±Ø§Ù†Ø´ Ø¨Ø§Ù„ÙƒÙŠØ¨Ù„', muscle: 'abs', goal: 'bulking', location: 'gym', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Weighted ab exercise for building thicker abs.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨Ø·Ù† Ø¨Ø§Ù„Ø£ÙˆØ²Ø§Ù† Ù„Ø¨Ù†Ø§Ø¡ Ø¨Ø·Ù† Ø£Ù‚ÙˆÙ‰.' },
  { id: 'bicycle-crunches', name: 'Bicycle Crunches', nameAr: 'ÙƒØ±Ø§Ù†Ø´ Ø§Ù„Ø¯Ø±Ø§Ø¬Ø©', muscle: 'abs', goal: 'cutting', location: 'home', gender: 'female', sets: 3, reps: '20 each', videoUrl: '', description: 'Great for waist definition and oblique toning.', descriptionAr: 'Ù…Ù…ØªØ§Ø² Ù„Ù†Ø­Øª Ø§Ù„Ø®ØµØ± ÙˆØªÙ†Ø³ÙŠÙ‚ Ø§Ù„Ø¹Ø¶Ù„Ø§Øª Ø§Ù„Ù…Ø§Ø¦Ù„Ø©.' },
  { id: 'dead-bug', name: 'Dead Bug', nameAr: 'Ø§Ù„Ø­Ø´Ø±Ø© Ø§Ù„Ù…ÙŠØªØ©', muscle: 'abs', goal: 'fitness', location: 'home', gender: 'female', sets: 3, reps: '10 each', videoUrl: '', description: 'Core stability exercise great for beginners.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø«Ø¨Ø§Øª Ø§Ù„Ø¬Ø°Ø¹ Ù…Ù…ØªØ§Ø² Ù„Ù„Ù…Ø¨ØªØ¯Ø¦ÙŠÙ†.' },

  // ===== QUADS =====
  { id: 'squats', name: 'Squats', nameAr: 'Ø§Ù„Ø³ÙƒÙˆØ§Øª', muscle: 'quads', goal: 'all', location: 'both', gender: 'all', sets: 4, reps: '10-12', videoUrl: '', description: 'King of leg exercises for overall lower body development.', descriptionAr: 'Ù…Ù„Ùƒ ØªÙ…Ø§Ø±ÙŠÙ† Ø§Ù„Ø£Ø±Ø¬Ù„ Ù„ØªØ·ÙˆÙŠØ± Ø§Ù„Ø¬Ø²Ø¡ Ø§Ù„Ø³ÙÙ„ÙŠ Ø¨Ø§Ù„ÙƒØ§Ù…Ù„.' },
  { id: 'leg-press', name: 'Leg Press', nameAr: 'Ø¶ØºØ· Ø§Ù„Ø£Ø±Ø¬Ù„', muscle: 'quads', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '10-12', videoUrl: '', description: 'Machine exercise for quad development with back support.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¢Ù„Ø© Ù„ØªØ·ÙˆÙŠØ± Ø§Ù„ÙØ®Ø° Ø§Ù„Ø£Ù…Ø§Ù…ÙŠ Ù…Ø¹ Ø¯Ø¹Ù… Ø§Ù„Ø¸Ù‡Ø±.' },
  { id: 'lunges', name: 'Lunges', nameAr: 'Ø§Ù„Ù„Ø§Ù†Ø¬', muscle: 'quads', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '12 each', videoUrl: '', description: 'Unilateral leg exercise for balance and quad strength.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø³Ø§Ù‚ Ø£Ø­Ø§Ø¯ÙŠ Ù„Ù„ØªÙˆØ§Ø²Ù† ÙˆÙ‚ÙˆØ© Ø§Ù„ÙØ®Ø°.' },
  { id: 'bulgarian-split-squats', name: 'Bulgarian Split Squats', nameAr: 'Ø³ÙƒÙˆØ§Øª Ø¨Ù„ØºØ§Ø±ÙŠ', muscle: 'quads', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '10 each', videoUrl: '', description: 'Single-leg exercise for quad strength and balance.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø³Ø§Ù‚ ÙˆØ§Ø­Ø¯Ø© Ù„Ù‚ÙˆØ© Ø§Ù„ÙØ®Ø° ÙˆØ§Ù„ØªÙˆØ§Ø²Ù†.' },
  { id: 'leg-extensions', name: 'Leg Extensions', nameAr: 'ØªÙ…Ø¯ÙŠØ¯ Ø§Ù„Ø£Ø±Ø¬Ù„', muscle: 'quads', goal: 'cutting', location: 'gym', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Isolation exercise targeting the quadriceps.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¹Ø²Ù„ ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„ÙØ®Ø° Ø§Ù„Ø£Ù…Ø§Ù…ÙŠ.' },
  { id: 'goblet-squats', name: 'Goblet Squats', nameAr: 'Ø³ÙƒÙˆØ§Øª Ø§Ù„ÙƒØ£Ø³', muscle: 'quads', goal: 'fitness', location: 'both', gender: 'female', sets: 3, reps: '12-15', videoUrl: '', description: 'Beginner-friendly squat variation with a dumbbell.', descriptionAr: 'Ø³ÙƒÙˆØ§Øª Ø³Ù‡Ù„ Ù„Ù„Ù…Ø¨ØªØ¯Ø¦ÙŠÙ† Ù…Ø¹ Ø¯Ù…Ø¨Ù„.' },
  { id: 'wall-sit', name: 'Wall Sit', nameAr: 'Ø§Ù„Ø¬Ù„ÙˆØ³ Ø¹Ù„Ù‰ Ø§Ù„Ø­Ø§Ø¦Ø·', muscle: 'quads', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '30-45 sec', videoUrl: '', description: 'Isometric exercise for quad endurance.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ù…ØªØ³Ø§ÙˆÙŠ Ø§Ù„Ù‚ÙŠØ§Ø³ Ù„ØªØ­Ù…Ù„ Ø§Ù„ÙØ®Ø°.' },

  // ===== HAMSTRINGS =====
  { id: 'romanian-deadlift', name: 'Romanian Deadlift', nameAr: 'Ø§Ù„Ø±ÙØ¹Ø© Ø§Ù„Ø±ÙˆÙ…Ø§Ù†ÙŠØ©', muscle: 'hamstrings', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '8-10', videoUrl: '', description: 'Hip hinge movement for hamstring and glute development.', descriptionAr: 'Ø­Ø±ÙƒØ© Ù…ÙØµÙ„ Ø§Ù„ÙˆØ±Ùƒ Ù„ØªØ·ÙˆÙŠØ± Ø§Ù„ÙØ®Ø° Ø§Ù„Ø®Ù„ÙÙŠ ÙˆØ§Ù„Ù…Ø¤Ø®Ø±Ø©.' },
  { id: 'glute-bridge', name: 'Glute Bridge', nameAr: 'Ø¬Ø³Ø± Ø§Ù„ØºÙ„ÙˆØª', muscle: 'hamstrings', goal: 'all', location: 'home', gender: 'all', sets: 3, reps: '15-20', videoUrl: '', description: 'Bodyweight exercise for glutes and hamstrings.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨ÙˆØ²Ù† Ø§Ù„Ø¬Ø³Ù… Ù„Ù„Ù…Ø¤Ø®Ø±Ø© ÙˆØ§Ù„ÙØ®Ø° Ø§Ù„Ø®Ù„ÙÙŠ.' },
  { id: 'leg-curls', name: 'Leg Curls', nameAr: 'Ø«Ù†ÙŠ Ø§Ù„Ø£Ø±Ø¬Ù„', muscle: 'hamstrings', goal: 'all', location: 'gym', gender: 'all', sets: 3, reps: '10-12', videoUrl: '', description: 'Machine exercise isolating the hamstrings.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¢Ù„Ø© Ù„Ø¹Ø²Ù„ Ø§Ù„ÙØ®Ø° Ø§Ù„Ø®Ù„ÙÙŠ.' },
  { id: 'nordic-curls', name: 'Nordic Curls', nameAr: 'Ø§Ù„ÙƒÙŠØ±Ù„ Ø§Ù„Ù†ÙˆØ±Ø¯ÙŠ', muscle: 'hamstrings', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '5-8', videoUrl: '', description: 'Advanced bodyweight exercise for hamstring strength.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ù…ØªÙ‚Ø¯Ù… Ø¨ÙˆØ²Ù† Ø§Ù„Ø¬Ø³Ù… Ù„Ù‚ÙˆØ© Ø§Ù„ÙØ®Ø° Ø§Ù„Ø®Ù„ÙÙŠ.' },
  { id: 'single-leg-bridge', name: 'Single Leg Bridge', nameAr: 'Ø¬Ø³Ø± Ø³Ø§Ù‚ ÙˆØ§Ø­Ø¯Ø©', muscle: 'hamstrings', goal: 'fitness', location: 'home', gender: 'female', sets: 3, reps: '12 each', videoUrl: '', description: 'Unilateral glute bridge for balanced hamstring development.', descriptionAr: 'Ø¬Ø³Ø± Ø£Ø­Ø§Ø¯ÙŠ Ù„ØªØ·ÙˆÙŠØ± Ù…ØªÙˆØ§Ø²Ù† Ù„Ù„ÙØ®Ø° Ø§Ù„Ø®Ù„ÙÙŠ.' },

  // ===== GLUTES =====
  { id: 'hip-thrust', name: 'Hip Thrust', nameAr: 'Ø¯ÙØ¹ Ø§Ù„ÙˆØ±Ùƒ', muscle: 'glutes', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '10-12', videoUrl: '', description: 'Best exercise for glute activation and growth.', descriptionAr: 'Ø£ÙØ¶Ù„ ØªÙ…Ø±ÙŠÙ† Ù„ØªÙØ¹ÙŠÙ„ ÙˆÙ†Ù…Ùˆ Ø§Ù„Ù…Ø¤Ø®Ø±Ø©.' },
  { id: 'donkey-kicks', name: 'Donkey Kicks', nameAr: 'Ø±ÙƒÙ„Ø© Ø§Ù„Ø­Ù…Ø§Ø±', muscle: 'glutes', goal: 'fitness', location: 'home', gender: 'female', sets: 3, reps: '15 each', videoUrl: '', description: 'Bodyweight glute isolation exercise.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¹Ø²Ù„ Ù„Ù„Ù…Ø¤Ø®Ø±Ø© Ø¨ÙˆØ²Ù† Ø§Ù„Ø¬Ø³Ù….' },
  { id: 'fire-hydrants', name: 'Fire Hydrants', nameAr: 'Ø­Ù†ÙÙŠØ© Ø§Ù„Ø­Ø±ÙŠÙ‚', muscle: 'glutes', goal: 'fitness', location: 'home', gender: 'female', sets: 3, reps: '15 each', videoUrl: '', description: 'Targets hip abductors and glutes for toning.', descriptionAr: 'ÙŠØ³ØªÙ‡Ø¯Ù Ø¹Ø¶Ù„Ø§Øª Ø§Ù„ÙˆØ±Ùƒ ÙˆØ§Ù„Ù…Ø¤Ø®Ø±Ø© Ù„Ù„ØªÙ†Ø´ÙŠÙ.' },
  { id: 'sumo-squats', name: 'Sumo Squats', nameAr: 'Ø³ÙƒÙˆØ§Øª Ø³ÙˆÙ…Ùˆ', muscle: 'glutes', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Wide stance squat emphasizing inner thighs and glutes.', descriptionAr: 'Ø³ÙƒÙˆØ§Øª Ø¨Ù‚Ø¯Ù…ÙŠÙ† ÙˆØ§Ø³Ø¹ØªÙŠÙ† ÙŠØ±ÙƒØ² Ø¹Ù„Ù‰ Ø§Ù„ÙØ®Ø° Ø§Ù„Ø¯Ø§Ø®Ù„ÙŠ ÙˆØ§Ù„Ù…Ø¤Ø®Ø±Ø©.' },
  { id: 'glute-kickback-machine', name: 'Glute Kickback Machine', nameAr: 'Ø¢Ù„Ø© Ø±ÙƒÙ„Ø© Ø§Ù„Ù…Ø¤Ø®Ø±Ø©', muscle: 'glutes', goal: 'all', location: 'gym', gender: 'female', sets: 3, reps: '12-15', videoUrl: '', description: 'Machine isolation for glute shaping and building.', descriptionAr: 'Ø¢Ù„Ø© Ø¹Ø²Ù„ Ù„Ù†Ø­Øª ÙˆØ¨Ù†Ø§Ø¡ Ø§Ù„Ù…Ø¤Ø®Ø±Ø©.' },
  { id: 'banded-walks', name: 'Banded Lateral Walks', nameAr: 'Ù…Ø´ÙŠ Ø¬Ø§Ù†Ø¨ÙŠ Ø¨Ø§Ù„Ø­Ø¨Ù„', muscle: 'glutes', goal: 'fitness', location: 'home', gender: 'female', sets: 3, reps: '15 each', videoUrl: '', description: 'Resistance band exercise for glute medius activation.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨Ø­Ø¨Ù„ Ù…Ø·Ø§Ø·ÙŠ Ù„ØªÙØ¹ÙŠÙ„ Ø¹Ø¶Ù„Ø© Ø§Ù„ÙˆØ±Ùƒ.' },
  { id: 'cable-pull-through', name: 'Cable Pull Through', nameAr: 'Ø³Ø­Ø¨ ÙƒÙŠØ¨Ù„ Ù…Ù† Ø¨ÙŠÙ† Ø§Ù„Ø£Ø±Ø¬Ù„', muscle: 'glutes', goal: 'bulking', location: 'gym', gender: 'all', sets: 3, reps: '12-15', videoUrl: '', description: 'Cable exercise targeting glutes and hamstrings.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† ÙƒÙŠØ¨Ù„ ÙŠØ³ØªÙ‡Ø¯Ù Ø§Ù„Ù…Ø¤Ø®Ø±Ø© ÙˆØ§Ù„ÙØ®Ø° Ø§Ù„Ø®Ù„ÙÙŠ.' },

  // ===== CALVES =====
  { id: 'calf-raises', name: 'Calf Raises', nameAr: 'Ø±ÙØ¹ Ø§Ù„Ø³Ù…Ø§Ù†Ø©', muscle: 'calves', goal: 'all', location: 'both', gender: 'all', sets: 3, reps: '15-20', videoUrl: '', description: 'Simple but effective exercise for calf development.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¨Ø³ÙŠØ· Ù„ÙƒÙ† ÙØ¹Ø§Ù„ Ù„ØªØ·ÙˆÙŠØ± Ø§Ù„Ø³Ù…Ø§Ù†Ø©.' },
  { id: 'seated-calf-raises', name: 'Seated Calf Raises', nameAr: 'Ø±ÙØ¹ Ø³Ù…Ø§Ù†Ø© Ø¬Ø§Ù„Ø³', muscle: 'calves', goal: 'bulking', location: 'gym', gender: 'all', sets: 4, reps: '12-15', videoUrl: '', description: 'Machine exercise targeting soleus muscle.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø¢Ù„Ø© ÙŠØ³ØªÙ‡Ø¯Ù Ø¹Ø¶Ù„Ø© Ø§Ù„Ø³Ù…Ø§Ù†Ø©.' },
  { id: 'jump-rope', name: 'Jump Rope', nameAr: 'Ù†Ø· Ø§Ù„Ø­Ø¨Ù„', muscle: 'calves', goal: 'cutting', location: 'home', gender: 'all', sets: 3, reps: '60 sec', videoUrl: '', description: 'Cardio exercise that builds calf endurance and burns fat.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ù‚Ù„Ø¨ÙŠ ÙŠØ¨Ù†ÙŠ ØªØ­Ù…Ù„ Ø§Ù„Ø³Ù…Ø§Ù†Ø© ÙˆÙŠØ­Ø±Ù‚ Ø§Ù„Ø¯Ù‡ÙˆÙ†.' },
  { id: 'single-leg-calf-raise', name: 'Single Leg Calf Raise', nameAr: 'Ø±ÙØ¹ Ø³Ù…Ø§Ù†Ø© Ø³Ø§Ù‚ ÙˆØ§Ø­Ø¯Ø©', muscle: 'calves', goal: 'fitness', location: 'home', gender: 'all', sets: 3, reps: '12 each', videoUrl: '', description: 'Unilateral calf exercise for balanced development.', descriptionAr: 'ØªÙ…Ø±ÙŠÙ† Ø³Ù…Ø§Ù†Ø© Ø£Ø­Ø§Ø¯ÙŠ Ù„ØªØ·ÙˆÙŠØ± Ù…ØªÙˆØ§Ø²Ù†.' },
];

export const exercises: Exercise[] = rawExercises.map((exercise) => ({
  ...exercise,
  name: repairMojibake(exercise.name),
  nameAr: repairMojibake(exercise.nameAr),
  description: repairMojibake(exercise.description),
  descriptionAr: repairMojibake(exercise.descriptionAr),
}));

export function getExercisesByFilters(
  selectedMuscles: string[],
  goal: string | null,
  location: string | null,
  gender: string | null = null
): Exercise[] {
  return exercises.filter((exercise) => {
    const muscleMatch = selectedMuscles.length === 0 || selectedMuscles.includes(exercise.muscle);
    const goalMatch = !goal || exercise.goal === 'all' || exercise.goal === goal;
    const locationMatch = !location || exercise.location === 'both' || exercise.location === location;
    const genderMatch = !gender || exercise.gender === 'all' || exercise.gender === gender;
    return muscleMatch && goalMatch && locationMatch && genderMatch;
  });
}


