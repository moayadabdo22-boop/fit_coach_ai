import type { Exercise } from './exercises';

type SourceGender = 'female' | 'male';
type SourceLocation = 'home' | 'gym';
type SourceGoal = 'build' | 'general';
type PreferredGender = 'female' | 'male' | null;

interface LocalClip {
  file: string;
  path: string;
  gender: SourceGender;
  muscle: string;
  location: SourceLocation;
  goal: SourceGoal;
}

const FEMALE_VIDEO_FILES = [
  'ErectorSpinae_BackExtension_Gym_Build_Female_1.mp4',
  'ErectorSpinae_BackExtension_Gym_Build_Female_2.mp4',
  'ErectorSpinae_BarbellDeadlift_Gym_General_Female_1.mp4',
  'ErectorSpinae_BarbellDeadlift_Gym_General_Female_2.mp4',
  'ErectorSpinae_BodyweightGoodMornings_Home_Build_Female_1.mp4',
  'ErectorSpinae_BodyweightGoodMornings_Home_Build_Female_2.mp4',
  'ErectorSpinae_SupermanHold_Home_General_Female_1.mp4',
  'ErectorSpinae_SupermanHold_Home_General_Female_2.mp4',
  'Gastrocnemius_BodyweightCalfRaise_Home_Build_Female_1.mp4',
  'Gastrocnemius_BodyweightCalfRaise_Home_Build_Female_2.mp4',
  'Gastrocnemius_SmithMachineCalfRaise_Gym_Build_Female_1.mp4',
  'Gastrocnemius_SmithMachineCalfRaise_Gym_Build_Female_2.mp4',
  'GluteusMaximus_BarbellHipThrust_Gym_Build_Female_1.mp4',
  'GluteusMaximus_BarbellHipThrust_Gym_Build_Female_2.mp4',
  'GluteusMaximus_BarbellSquat_Gym_General_Female_1.mp4',
  'GluteusMaximus_BarbellSquat_Gym_General_Female_2.mp4',
  'GluteusMaximus_BodyweightWaitersBow_Home_Build_Female_1.mp4',
  'GluteusMaximus_BodyweightWaitersBow_Home_Build_Female_2.mp4',
  'GluteusMaximus_BoxJump_Home_General_Female_1.mp4',
  'GluteusMaximus_BoxJump_Home_General_Female_2.mp4',
  'GluteusMedius_BarbellSquat_Gym_General_Female_1.mp4',
  'GluteusMedius_BarbellSquat_Gym_General_Female_2.mp4',
  'GluteusMedius_MachineGluteKickback_Gym_Build_Female_1.mp4',
  'GluteusMedius_MachineGluteKickback_Gym_Build_Female_2.mp4',
  'GluteusMedius_SingleLeggedRomanianDeadlifts_Home_General_Female_1.mp4',
  'GluteusMedius_SingleLeggedRomanianDeadlifts_Home_General_Female_2.mp4',
  'Hamstrings_BarbellStiffLegDeadlifts_Gym_Build_Female_1.mp4',
  'Hamstrings_BarbellStiffLegDeadlifts_Gym_Build_Female_2.mp4',
  'Hamstrings_BodyweightWaitersBow_Home_General_Female_1.mp4',
  'Hamstrings_BodyweightWaitersBow_Home_General_Female_2.mp4',
  'Hamstrings_LandmineRomanianDeadlift_Gym_General_Female_1.mp4',
  'Hamstrings_LandmineRomanianDeadlift_Gym_General_Female_2.mp4',
  'Hamstrings_SingleLeggedRomanianDeadlifts_Home_Build_Female_1.mp4',
  'Hamstrings_SingleLeggedRomanianDeadlifts_Home_Build_Female_2.mp4',
  'LatissimusDorsi_BodyweightSupermanRow_Home_Build_Female_1.mp4',
  'LatissimusDorsi_BodyweightSupermanRow_Home_Build_Female_2.mp4',
  'LatissimusDorsi_LatPulldown_Gym_Build_Female_1.mp4',
  'LatissimusDorsi_LatPulldown_Gym_Build_Female_2.mp4',
  'LatissimusDorsi_SeatedCableRow_Gym_General_Female_1.mp4',
  'LatissimusDorsi_SeatedCableRow_Gym_General_Female_2.mp4',
  'LatissimusDorsi_SupermanHold_Home_General_Female_1.mp4',
  'LatissimusDorsi_SupermanHold_Home_General_Female_2.mp4',
  'PosteriorDeltoid_BodyweightReverseFly_Home_Build_Female_1.mp4',
  'PosteriorDeltoid_BodyweightReverseFly_Home_Build_Female_2.mp4',
  'PosteriorDeltoid_FacePull_Gym_General_Female_1.mp4',
  'PosteriorDeltoid_FacePull_Gym_General_Female_2.mp4',
  'PosteriorDeltoid_ReversePecDeck_Gym_Build_Female_1.mp4',
  'PosteriorDeltoid_ReversePecDeck_Gym_Build_Female_2.mp4',
  'PosteriorDeltoid_SupermanHold_Home_General_Female_1.mp4',
  'PosteriorDeltoid_SupermanHold_Home_General_Female_2.mp4',
  'Soleus_BodyweightCalfRaise_Home_Build_Female_1.mp4',
  'Soleus_BodyweightCalfRaise_Home_Build_Female_2.mp4',
  'Soleus_SeatedCalfRaise_Gym_Build_Female_1.mp4',
  'Soleus_SeatedCalfRaise_Gym_Build_Female_2.mp4',
  'Soleus_SmithMachineCalfRaise_Gym_General_Female_1.mp4',
  'Soleus_SmithMachineCalfRaise_Gym_General_Female_2.mp4',
  'TeresMajor_BodyweightReverseFly_Home_Build_Female_1.mp4',
  'TeresMajor_BodyweightReverseFly_Home_Build_Female_2.mp4',
  'TeresMajor_LatPulldown_Gym_Build_Female_1.mp4',
  'TeresMajor_LatPulldown_Gym_Build_Female_2.mp4',
  'TeresMajor_SeatedCableRow_Gym_General_Female_1.mp4',
  'TeresMajor_SeatedCableRow_Gym_General_Female_2.mp4',
  'TeresMajor_SupermanHold_Home_General_Female_1.mp4',
  'TeresMajor_SupermanHold_Home_General_Female_2.mp4',
  'TeresMinor_BodyweightExternalRotation_Home_Build_Female_1.mp4',
  'TeresMinor_BodyweightExternalRotation_Home_Build_Female_2.mp4',
  'TeresMinor_CableExternalRotation_Gym_Build_Female_1.mp4',
  'TeresMinor_CableExternalRotation_Gym_Build_Female_2.mp4',
  'TeresMinor_FacePull_Gym_General_Female_1.mp4',
  'TeresMinor_FacePull_Gym_General_Female_2.mp4',
  'TeresMinor_SupermanHold_Home_General_Female_1.mp4',
  'TeresMinor_SupermanHold_Home_General_Female_2.mp4',
  'Trapezius_BarbellShrug_Gym_Build_Female_1.mp4',
  'Trapezius_BarbellShrug_Gym_Build_Female_2.mp4',
  'Trapezius_BodyweightShrug_Home_Build_Female_1.mp4',
  'Trapezius_BodyweightShrug_Home_Build_Female_2.mp4',
  'Trapezius_FacePull_Gym_General_Female_1.mp4',
  'Trapezius_FacePull_Gym_General_Female_2.mp4',
  'Trapezius_SupermanHold_Home_General_Female_1.mp4',
  'Trapezius_SupermanHold_Home_General_Female_2.mp4',
  'TricepsLateralHead_BodyweightTricepExtension_Home_Build_Female_1.mp4',
  'TricepsLateralHead_BodyweightTricepExtension_Home_Build_Female_2.mp4',
  'TricepsLateralHead_CloseGripBenchPress_Gym_General_Female_1.mp4',
  'TricepsLateralHead_CloseGripBenchPress_Gym_General_Female_2.mp4',
  'TricepsLateralHead_DiamondPushUp_Home_General_Female_1.mp4',
  'TricepsLateralHead_DiamondPushUp_Home_General_Female_2.mp4',
  'TricepsLateralHead_TricepPushdown_Gym_Build_Female_1.mp4',
  'TricepsLateralHead_TricepPushdown_Gym_Build_Female_2.mp4',
  'TricepsLongHead_BodyweightTricepExtension_Home_Build_Female_1.mp4',
  'TricepsLongHead_BodyweightTricepExtension_Home_Build_Female_2.mp4',
  'TricepsLongHead_CableOverheadTricepExtension_Gym_Build_Female_1.mp4',
  'TricepsLongHead_CableOverheadTricepExtension_Gym_Build_Female_2.mp4',
  'TricepsLongHead_DiamondPushUp_Home_General_Female_1.mp4',
  'TricepsLongHead_DiamondPushUp_Home_General_Female_2.mp4',
  'TricepsLongHead_TricepPushdown_Gym_General_Female_1.mp4',
  'TricepsLongHead_TricepPushdown_Gym_General_Female_2.mp4',
  'TricepsMedialHead_BodyweightTricepExtension_Home_Build_Female_1.mp4',
  'TricepsMedialHead_BodyweightTricepExtension_Home_Build_Female_2.mp4',
  'TricepsMedialHead_CloseGripBenchPress_Gym_General_Female_1.mp4',
  'TricepsMedialHead_CloseGripBenchPress_Gym_General_Female_2.mp4',
  'TricepsMedialHead_DiamondPushUp_Home_General_Female_1.mp4',
  'TricepsMedialHead_DiamondPushUp_Home_General_Female_2.mp4',
  'TricepsMedialHead_ReverseGripTricepPushdown_Gym_Build_Female_1.mp4',
  'TricepsMedialHead_ReverseGripTricepPushdown_Gym_Build_Female_2.mp4',
] as const;

const MALE_VIDEO_FILES = [
  'ErectorSpinae_BackExtension_Gym_Build_Male_1.mp4',
  'ErectorSpinae_BackExtension_Gym_Build_Male_2.mp4',
  'ErectorSpinae_BarbellDeadlift_Gym_General_Male_1.mp4',
  'ErectorSpinae_BarbellDeadlift_Gym_General_Male_2.mp4',
  'ErectorSpinae_BodyweightGoodMornings_Home_Build_Male_1.mp4',
  'ErectorSpinae_BodyweightGoodMornings_Home_Build_Male_2.mp4',
  'ErectorSpinae_SupermanHold_Home_General_Male_1.mp4',
  'ErectorSpinae_SupermanHold_Home_General_Male_2.mp4',
  'Gastrocnemius_BodyweightCalfRaise_Home_Build_Male_1.mp4',
  'Gastrocnemius_BodyweightCalfRaise_Home_Build_Male_2.mp4',
  'Gastrocnemius_SmithMachineCalfRaise_Gym_Build_Male_1.mp4',
  'Gastrocnemius_SmithMachineCalfRaise_Gym_Build_Male_2.mp4',
  'GluteusMaximus_BarbellHipThrust_Gym_Build_Male_1.mp4',
  'GluteusMaximus_BarbellHipThrust_Gym_Build_Male_2.mp4',
  'GluteusMaximus_BarbellSquat_Gym_General_Male_1.mp4',
  'GluteusMaximus_BarbellSquat_Gym_General_Male_2.mp4',
  'GluteusMaximus_BodyweightWaitersBow_Home_Build_Male_1.mp4',
  'GluteusMaximus_BodyweightWaitersBow_Home_Build_Male_2.mp4',
  'GluteusMaximus_BoxJump_Home_General_Male_1.mp4',
  'GluteusMaximus_BoxJump_Home_General_Male_2.mp4',
  'GluteusMedius_BarbellSquat_Gym_General_Male_1.mp4',
  'GluteusMedius_BarbellSquat_Gym_General_Male_2.mp4',
  'GluteusMedius_BodyweightStaggeredWaitersBow_Home_Build_Female_1.mp4',
  'GluteusMedius_BodyweightStaggeredWaitersBow_Home_Build_Female_2.mp4',
  'GluteusMedius_BodyweightStaggeredWaitersBow_Home_Build_Male_1.mp4',
  'GluteusMedius_BodyweightStaggeredWaitersBow_Home_Build_Male_2.mp4',
  'GluteusMedius_MachineGluteKickback_Gym_Build_Male_1.mp4',
  'GluteusMedius_MachineGluteKickback_Gym_Build_Male_2.mp4',
  'GluteusMedius_SingleLeggedRomanianDeadlifts_Home_General_Male_1.mp4',
  'GluteusMedius_SingleLeggedRomanianDeadlifts_Home_General_Male_2.mp4',
  'Hamstrings_BarbellStiffLegDeadlifts_Gym_Build_Male_1.mp4',
  'Hamstrings_BarbellStiffLegDeadlifts_Gym_Build_Male_2.mp4',
  'Hamstrings_BodyweightWaitersBow_Home_General_Male_1.mp4',
  'Hamstrings_BodyweightWaitersBow_Home_General_Male_2.mp4',
  'Hamstrings_LandmineRomanianDeadlift_Gym_General_Male_1.mp4',
  'Hamstrings_LandmineRomanianDeadlift_Gym_General_Male_2.mp4',
  'Hamstrings_SingleLeggedRomanianDeadlifts_Home_Build_Male_1.mp4',
  'Hamstrings_SingleLeggedRomanianDeadlifts_Home_Build_Male_2.mp4',
  'LatissimusDorsi_BodyweightSupermanRow_Home_Build_Male_1.mp4',
  'LatissimusDorsi_BodyweightSupermanRow_Home_Build_Male_2.mp4',
  'LatissimusDorsi_LatPulldown_Gym_Build_Male_1.mp4',
  'LatissimusDorsi_LatPulldown_Gym_Build_Male_2.mp4',
  'LatissimusDorsi_SeatedCableRow_Gym_General_Male_1.mp4',
  'LatissimusDorsi_SeatedCableRow_Gym_General_Male_2.mp4',
  'LatissimusDorsi_SupermanHold_Home_General_Male_1.mp4',
  'LatissimusDorsi_SupermanHold_Home_General_Male_2.mp4',
  'PosteriorDeltoid_BodyweightReverseFly_Home_Build_Male_1.mp4',
  'PosteriorDeltoid_BodyweightReverseFly_Home_Build_Male_2.mp4',
  'PosteriorDeltoid_FacePull_Gym_General_Male_1.mp4',
  'PosteriorDeltoid_FacePull_Gym_General_Male_2.mp4',
  'PosteriorDeltoid_ReversePecDeck_Gym_Build_Male_1.mp4',
  'PosteriorDeltoid_ReversePecDeck_Gym_Build_Male_2.mp4',
  'PosteriorDeltoid_SupermanHold_Home_General_Male_1.mp4',
  'PosteriorDeltoid_SupermanHold_Home_General_Male_2.mp4',
  'Soleus_BodyweightCalfRaise_Home_Build_Male_1.mp4',
  'Soleus_BodyweightCalfRaise_Home_Build_Male_2.mp4',
  'Soleus_SeatedCalfRaise_Gym_Build_Male_1.mp4',
  'Soleus_SeatedCalfRaise_Gym_Build_Male_2.mp4',
  'Soleus_SmithMachineCalfRaise_Gym_General_Male_1.mp4',
  'Soleus_SmithMachineCalfRaise_Gym_General_Male_2.mp4',
  'TeresMajor_BodyweightReverseFly_Home_Build_Male_1.mp4',
  'TeresMajor_BodyweightReverseFly_Home_Build_Male_2.mp4',
  'TeresMajor_LatPulldown_Gym_Build_Male_1.mp4',
  'TeresMajor_LatPulldown_Gym_Build_Male_2.mp4',
  'TeresMajor_SeatedCableRow_Gym_General_Male_1.mp4',
  'TeresMajor_SeatedCableRow_Gym_General_Male_2.mp4',
  'TeresMajor_SupermanHold_Home_General_Male_1.mp4',
  'TeresMajor_SupermanHold_Home_General_Male_2.mp4',
  'TeresMinor_BodyweightExternalRotation_Home_Build_Male_1.mp4',
  'TeresMinor_BodyweightExternalRotation_Home_Build_Male_2.mp4',
  'TeresMinor_CableExternalRotation_Gym_Build_Male_1.mp4',
  'TeresMinor_CableExternalRotation_Gym_Build_Male_2.mp4',
  'TeresMinor_FacePull_Gym_General_Male_1.mp4',
  'TeresMinor_FacePull_Gym_General_Male_2.mp4',
  'TeresMinor_SupermanHold_Home_General_Male_1.mp4',
  'TeresMinor_SupermanHold_Home_General_Male_2.mp4',
  'Trapezius_BarbellShrug_Gym_Build_Male_1.mp4',
  'Trapezius_BarbellShrug_Gym_Build_Male_2.mp4',
  'Trapezius_BodyweightShrug_Home_Build_Male_1.mp4',
  'Trapezius_BodyweightShrug_Home_Build_Male_2.mp4',
  'Trapezius_FacePull_Gym_General_Male_1.mp4',
  'Trapezius_FacePull_Gym_General_Male_2.mp4',
  'Trapezius_SupermanHold_Home_General_Male_1.mp4',
  'Trapezius_SupermanHold_Home_General_Male_2.mp4',
  'TricepsLateralHead_BodyweightTricepExtension_Home_Build_Male_1.mp4',
  'TricepsLateralHead_BodyweightTricepExtension_Home_Build_Male_2.mp4',
  'TricepsLateralHead_CloseGripBenchPress_Gym_General_Male_1.mp4',
  'TricepsLateralHead_CloseGripBenchPress_Gym_General_Male_2.mp4',
  'TricepsLateralHead_DiamondPushUp_Home_General_Male_1.mp4',
  'TricepsLateralHead_DiamondPushUp_Home_General_Male_2.mp4',
  'TricepsLateralHead_TricepPushdown_Gym_Build_Male_1.mp4',
  'TricepsLateralHead_TricepPushdown_Gym_Build_Male_2.mp4',
  'TricepsLongHead_BodyweightTricepExtension_Home_Build_Male_1.mp4',
  'TricepsLongHead_BodyweightTricepExtension_Home_Build_Male_2.mp4',
  'TricepsLongHead_CableOverheadTricepExtension_Gym_Build_Male_1.mp4',
  'TricepsLongHead_CableOverheadTricepExtension_Gym_Build_Male_2.mp4',
  'TricepsLongHead_DiamondPushUp_Home_General_Male_1.mp4',
  'TricepsLongHead_DiamondPushUp_Home_General_Male_2.mp4',
  'TricepsLongHead_TricepPushdown_Gym_General_Male_1.mp4',
  'TricepsLongHead_TricepPushdown_Gym_General_Male_2.mp4',
  'TricepsMedialHead_BodyweightTricepExtension_Home_Build_Male_1.mp4',
  'TricepsMedialHead_BodyweightTricepExtension_Home_Build_Male_2.mp4',
  'TricepsMedialHead_CloseGripBenchPress_Gym_General_Male_1.mp4',
  'TricepsMedialHead_CloseGripBenchPress_Gym_General_Male_2.mp4',
  'TricepsMedialHead_DiamondPushUp_Home_General_Male_1.mp4',
  'TricepsMedialHead_DiamondPushUp_Home_General_Male_2.mp4',
  'TricepsMedialHead_ReverseGripTricepPushdown_Gym_Build_Male_1.mp4',
  'TricepsMedialHead_ReverseGripTricepPushdown_Gym_Build_Male_2.mp4',
] as const;

const parseClip = (file: string, gender: SourceGender): LocalClip => {
  const baseName = file.replace(/\.mp4$/i, '');
  const parts = baseName.split('_');
  const muscle = parts[0] ?? 'General';
  const location: SourceLocation = parts.includes('Home') ? 'home' : 'gym';
  const goal: SourceGoal = parts.includes('General') ? 'general' : 'build';

  return {
    file,
    path: `/videos/back-muscles/${gender}/${file}`,
    gender,
    muscle,
    location,
    goal,
  };
};

const ALL_CLIPS: LocalClip[] = [
  ...FEMALE_VIDEO_FILES.map((file) => parseClip(file, 'female')),
  ...MALE_VIDEO_FILES.map((file) => parseClip(file, 'male')),
];

const MUSCLE_TO_SOURCE_MUSCLES: Record<Exercise['muscle'], string[]> = {
  chest: [],
  back: ['LatissimusDorsi', 'ErectorSpinae', 'TeresMajor', 'TeresMinor', 'Trapezius', 'PosteriorDeltoid'],
  shoulders: ['PosteriorDeltoid', 'Trapezius'],
  biceps: [],
  triceps: ['TricepsLongHead', 'TricepsLateralHead', 'TricepsMedialHead'],
  abs: [],
  quads: [],
  hamstrings: ['Hamstrings'],
  glutes: ['GluteusMaximus', 'GluteusMedius'],
  calves: ['Gastrocnemius', 'Soleus'],
};

const goalToSourceGoal = (goal: Exercise['goal']): SourceGoal | null => {
  if (goal === 'bulking') {
    return 'build';
  }

  if (goal === 'cutting' || goal === 'fitness') {
    return 'general';
  }

  return null;
};

const hashString = (value: string): number => {
  let hash = 0;

  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }

  return Math.abs(hash);
};

const pickDeterministicClip = (clips: LocalClip[], seed: string): LocalClip | null => {
  if (clips.length === 0) {
    return null;
  }

  const index = hashString(seed) % clips.length;
  return clips[index];
};

export function getExerciseVideoUrl(exercise: Exercise, preferredGender: PreferredGender = null): string {
  const preferredMuscles = MUSCLE_TO_SOURCE_MUSCLES[exercise.muscle] ?? [];
  if (preferredMuscles.length === 0) {
    return '';
  }

  const preferredGoal = goalToSourceGoal(exercise.goal);
  const requestedGender: PreferredGender =
    preferredGender ?? (exercise.gender === 'all' ? null : exercise.gender);

  const clipsByGender =
    requestedGender === null
      ? ALL_CLIPS
      : ALL_CLIPS.filter((clip) => clip.gender === requestedGender);

  const byMuscle = clipsByGender.filter((clip) => preferredMuscles.includes(clip.muscle));
  if (byMuscle.length === 0) {
    return '';
  }

  const byLocation =
    exercise.location === 'both'
      ? byMuscle
      : byMuscle.filter((clip) => clip.location === exercise.location);
  const byGoal = preferredGoal ? byLocation.filter((clip) => clip.goal === preferredGoal) : byLocation;

  const anyGenderByMuscle = ALL_CLIPS.filter((clip) => preferredMuscles.includes(clip.muscle));
  const anyGenderByLocation =
    exercise.location === 'both'
      ? anyGenderByMuscle
      : anyGenderByMuscle.filter((clip) => clip.location === exercise.location);
  const anyGenderByGoal = preferredGoal
    ? anyGenderByLocation.filter((clip) => clip.goal === preferredGoal)
    : anyGenderByLocation;

  const candidatePools: LocalClip[][] = [
    byGoal,
    byLocation,
    byMuscle,
    anyGenderByGoal,
    anyGenderByLocation,
    anyGenderByMuscle,
  ];

  for (const pool of candidatePools) {
    const clip = pickDeterministicClip(pool, exercise.id);
    if (clip) {
      return clip.path;
    }
  }

  return '';
}

export function isLocalExerciseVideo(videoUrl: string): boolean {
  return videoUrl.startsWith('/videos/back-muscles/');
}
