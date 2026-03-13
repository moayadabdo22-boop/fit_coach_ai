import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useUser } from '@/contexts/UserContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { repairMojibake } from '@/lib/text';
import femaleFrontBase from '@/assets/anatomy/female/front/normal/base-transparent.png';
import femaleFrontAbsRaw from '@/assets/anatomy/female/front/normal/abs.svg?raw';
import femaleFrontBicepsLeftRaw from '@/assets/anatomy/female/front/normal/biceps-left.svg?raw';
import femaleFrontBicepsRightRaw from '@/assets/anatomy/female/front/normal/biceps-right.svg?raw';
import femaleFrontForearmLeftRaw from '@/assets/anatomy/female/front/normal/forearm-left.svg?raw';
import femaleFrontForearmRightRaw from '@/assets/anatomy/female/front/normal/forearm-right.svg?raw';
import femaleFrontHandsLeftRaw from '@/assets/anatomy/female/front/normal/hands-left.svg?raw';
import femaleFrontHandsRightRaw from '@/assets/anatomy/female/front/normal/hands-right.svg?raw';
import femaleFrontChestLeftRaw from '@/assets/anatomy/female/front/normal/chest-left.svg?raw';
import femaleFrontChestRightRaw from '@/assets/anatomy/female/front/normal/chest-right.svg?raw';
import femaleFrontAbsSideLeftRaw from '@/assets/anatomy/female/front/normal/abs-side-left.svg?raw';
import femaleFrontAbsSideRightRaw from '@/assets/anatomy/female/front/normal/abs-side-right.svg?raw';
import femaleFrontNeck1Raw from '@/assets/anatomy/female/front/normal/neck-1.svg?raw';
import femaleFrontNeck2Raw from '@/assets/anatomy/female/front/normal/neck-2.svg?raw';
import femaleFrontQuadLeftRaw from '@/assets/anatomy/female/front/normal/quad-left.svg?raw';
import femaleFrontQuadRightRaw from '@/assets/anatomy/female/front/normal/quad-right.svg?raw';
import femaleFrontShinLeftRaw from '@/assets/anatomy/female/front/normal/shin-left.svg?raw';
import femaleFrontShinRightRaw from '@/assets/anatomy/female/front/normal/shin-right.svg?raw';
import femaleFrontShoulderLeftRaw from '@/assets/anatomy/female/front/normal/shoulder-left.svg?raw';
import femaleFrontShoulderRightRaw from '@/assets/anatomy/female/front/normal/shoulder-right.svg?raw';
import femaleFrontAdvancedBase from '@/assets/anatomy/female/front/advanced/base-transparent.png';
import femaleFrontAdvancedAbsUpRaw from '@/assets/anatomy/female/front/advanced/abs-up.svg?raw';
import femaleFrontAdvancedAbsDownRaw from '@/assets/anatomy/female/front/advanced/abs-down.svg?raw';
import femaleFrontAdvancedAnteriorDeltoidLeftRaw from '@/assets/anatomy/female/front/advanced/anterior-deltoid-left.svg?raw';
import femaleFrontAdvancedAnteriorDeltoidRightRaw from '@/assets/anatomy/female/front/advanced/anterior-deltoid-right.svg?raw';
import femaleFrontAdvancedLateralDeltoidLeftRaw from '@/assets/anatomy/female/front/advanced/lateral-deltoid-left.svg?raw';
import femaleFrontAdvancedLateralDeltoidRightRaw from '@/assets/anatomy/female/front/advanced/lateral-deltoid-right.svg?raw';
import femaleFrontAdvancedUpperPectoralisLeftRaw from '@/assets/anatomy/female/front/advanced/upper-pectoralis-left.svg?raw';
import femaleFrontAdvancedUpperPectoralisRightRaw from '@/assets/anatomy/female/front/advanced/upper-pectoralis-right.svg?raw';
import femaleFrontAdvancedMidLowerPectoralisLeftRaw from '@/assets/anatomy/female/front/advanced/mid-lower-pectoralis-left.svg?raw';
import femaleFrontAdvancedMidLowerPectoralisRightRaw from '@/assets/anatomy/female/front/advanced/mid-lower-pectoralis-right.svg?raw';
import femaleFrontAdvancedLongHeadBicepLeftRaw from '@/assets/anatomy/female/front/advanced/long-head-bicep-left.svg?raw';
import femaleFrontAdvancedLongHeadBicepRightRaw from '@/assets/anatomy/female/front/advanced/long-head-bicep-right.svg?raw';
import femaleFrontAdvancedShortHeadBicepLeftRaw from '@/assets/anatomy/female/front/advanced/short-head-bicep-left.svg?raw';
import femaleFrontAdvancedShortHeadBicepRightRaw from '@/assets/anatomy/female/front/advanced/short-head-bicep-right.svg?raw';
import femaleFrontAdvancedSideAbsLeftRaw from '@/assets/anatomy/female/front/advanced/side-abs-left.svg?raw';
import femaleFrontAdvancedSideAbsRightRaw from '@/assets/anatomy/female/front/advanced/side-abs-right.svg?raw';
import femaleFrontAdvancedNeckCenterRaw from '@/assets/anatomy/female/front/advanced/neck-center.svg?raw';
import femaleFrontAdvancedNeckLeftRaw from '@/assets/anatomy/female/front/advanced/neck-left.svg?raw';
import femaleFrontAdvancedNeckRightRaw from '@/assets/anatomy/female/front/advanced/neck-right.svg?raw';
import femaleFrontAdvancedWristExtensorsLeftRaw from '@/assets/anatomy/female/front/advanced/wrist-extensors-left.svg?raw';
import femaleFrontAdvancedWristExtensorsRightRaw from '@/assets/anatomy/female/front/advanced/wrist-extensors-right.svg?raw';
import femaleFrontAdvancedWristFlexorsLeftRaw from '@/assets/anatomy/female/front/advanced/wrist-flexors-left.svg?raw';
import femaleFrontAdvancedWristFlexorsRightRaw from '@/assets/anatomy/female/front/advanced/wrist-flexors-right.svg?raw';
import femaleFrontAdvancedHandsLeftRaw from '@/assets/anatomy/female/front/advanced/hands-left.svg?raw';
import femaleFrontAdvancedHandsRightRaw from '@/assets/anatomy/female/front/advanced/hands-right.svg?raw';
import femaleFrontAdvancedRectusFemorisLeftRaw from '@/assets/anatomy/female/front/advanced/rectus-femoris-left.svg?raw';
import femaleFrontAdvancedRectusFemorisRightRaw from '@/assets/anatomy/female/front/advanced/rectus-femoris-right.svg?raw';
import femaleFrontAdvancedOuterQuadricepLeftRaw from '@/assets/anatomy/female/front/advanced/outer-quadricep-left.svg?raw';
import femaleFrontAdvancedOuterQuadricepRightRaw from '@/assets/anatomy/female/front/advanced/outer-quadricep-right.svg?raw';
import femaleFrontAdvancedInnerQuadricepLeftRaw from '@/assets/anatomy/female/front/advanced/inner-quadricep-left.svg?raw';
import femaleFrontAdvancedInnerQuadricepRightRaw from '@/assets/anatomy/female/front/advanced/inner-quadricep-right.svg?raw';
import femaleFrontAdvancedInnerThighLeftRaw from '@/assets/anatomy/female/front/advanced/inner-thigh-left.svg?raw';
import femaleFrontAdvancedInnerThighRightRaw from '@/assets/anatomy/female/front/advanced/inner-thigh-right.svg?raw';
import femaleFrontAdvancedSoleusLeftRaw from '@/assets/anatomy/female/front/advanced/soleus-left.svg?raw';
import femaleFrontAdvancedSoleusRightRaw from '@/assets/anatomy/female/front/advanced/soleus-right.svg?raw';
import femaleFrontAdvancedTibialisLeftRaw from '@/assets/anatomy/female/front/advanced/tibialis-left.svg?raw';
import femaleFrontAdvancedTibialisRightRaw from '@/assets/anatomy/female/front/advanced/tibialis-right.svg?raw';
import femaleFrontAdvancedGastrocnemiusLeftRaw from '@/assets/anatomy/female/front/advanced/gastrocnemius-left.svg?raw';
import femaleFrontAdvancedGastrocnemiusRightRaw from '@/assets/anatomy/female/front/advanced/gastrocnemius-right.svg?raw';
import femaleFrontAdvancedFeetLeftRaw from '@/assets/anatomy/female/front/advanced/feet-left.svg?raw';
import femaleFrontAdvancedFeetRightRaw from '@/assets/anatomy/female/front/advanced/feet-right.svg?raw';
import femaleFrontAdvancedGroinRaw from '@/assets/anatomy/female/front/advanced/groin.svg?raw';
import femaleBackAdvancedBase from '@/assets/anatomy/female/back/advanced/base-transparent.png';
import femaleBackAdvancedNeckRaw from '@/assets/anatomy/female/back/advanced/neck.svg?raw';
import femaleBackAdvancedUpperTrapeziusRaw from '@/assets/anatomy/female/back/advanced/upper-trapezius.svg?raw';
import femaleBackAdvancedTrapsMiddleRaw from '@/assets/anatomy/female/back/advanced/traps-middle.svg?raw';
import femaleBackAdvancedLowerTrapeziusRaw from '@/assets/anatomy/female/back/advanced/lower-trapezius.svg?raw';
import femaleBackAdvancedLateralDeltoidLeftRaw from '@/assets/anatomy/female/back/advanced/lateral-deltoid-left.svg?raw';
import femaleBackAdvancedLateralDeltoidRightRaw from '@/assets/anatomy/female/back/advanced/lateral-deltoid-right.svg?raw';
import femaleBackAdvancedPosteriorDeltoidLeftRaw from '@/assets/anatomy/female/back/advanced/posterior-deltoid-left.svg?raw';
import femaleBackAdvancedPosteriorDeltoidRightRaw from '@/assets/anatomy/female/back/advanced/posterior-deltoid-right.svg?raw';
import femaleBackAdvancedLongHeadTricepsLeftRaw from '@/assets/anatomy/female/back/advanced/long-head-triceps-left.svg?raw';
import femaleBackAdvancedLongHeadTricepsRightRaw from '@/assets/anatomy/female/back/advanced/long-head-triceps-right.svg?raw';
import femaleBackAdvancedLateralHeadTricepsLeftRaw from '@/assets/anatomy/female/back/advanced/lateral-head-triceps-left.svg?raw';
import femaleBackAdvancedLateralHeadTricepsRightRaw from '@/assets/anatomy/female/back/advanced/lateral-head-triceps-right.svg?raw';
import femaleBackAdvancedMedialHeadTricepsLeftRaw from '@/assets/anatomy/female/back/advanced/medial-head-triceps-left.svg?raw';
import femaleBackAdvancedMedialHeadTricepsRightRaw from '@/assets/anatomy/female/back/advanced/medial-head-triceps-right.svg?raw';
import femaleBackAdvancedWristExtensorsLeftRaw from '@/assets/anatomy/female/back/advanced/wrist-extensors-left.svg?raw';
import femaleBackAdvancedWristExtensorsRightRaw from '@/assets/anatomy/female/back/advanced/wrist-extensors-right.svg?raw';
import femaleBackAdvancedWristFlexorsLeftRaw from '@/assets/anatomy/female/back/advanced/wrist-flexors-left.svg?raw';
import femaleBackAdvancedWristFlexorsRightRaw from '@/assets/anatomy/female/back/advanced/wrist-flexors-right.svg?raw';
import femaleBackAdvancedHandsLeftRaw from '@/assets/anatomy/female/back/advanced/hands-left.svg?raw';
import femaleBackAdvancedHandsRightRaw from '@/assets/anatomy/female/back/advanced/hands-right.svg?raw';
import femaleBackAdvancedLatsLeftRaw from '@/assets/anatomy/female/back/advanced/lats-left.svg?raw';
import femaleBackAdvancedLatsRightRaw from '@/assets/anatomy/female/back/advanced/lats-right.svg?raw';
import femaleBackAdvancedLowerBackRaw from '@/assets/anatomy/female/back/advanced/lower-back.svg?raw';
import femaleBackAdvancedGluteusMediusLeftRaw from '@/assets/anatomy/female/back/advanced/gluteus-medius-left.svg?raw';
import femaleBackAdvancedGluteusMediusRightRaw from '@/assets/anatomy/female/back/advanced/gluteus-medius-right.svg?raw';
import femaleBackAdvancedGluteusMaximusLeftRaw from '@/assets/anatomy/female/back/advanced/gluteus-maximus-left.svg?raw';
import femaleBackAdvancedGluteusMaximusRightRaw from '@/assets/anatomy/female/back/advanced/gluteus-maximus-right.svg?raw';
import femaleBackAdvancedInnerThighLeftRaw from '@/assets/anatomy/female/back/advanced/inner-thigh-left.svg?raw';
import femaleBackAdvancedInnerThighRightRaw from '@/assets/anatomy/female/back/advanced/inner-thigh-right.svg?raw';
import femaleBackAdvancedMedialHamstringsLeftRaw from '@/assets/anatomy/female/back/advanced/medial-hamstrings-left.svg?raw';
import femaleBackAdvancedMedialHamstringsRightRaw from '@/assets/anatomy/female/back/advanced/medial-hamstrings-right.svg?raw';
import femaleBackAdvancedLateralHamstringsLeftRaw from '@/assets/anatomy/female/back/advanced/lateral-hamstrings-left.svg?raw';
import femaleBackAdvancedLateralHamstringsRightRaw from '@/assets/anatomy/female/back/advanced/lateral-hamstrings-right.svg?raw';
import femaleBackAdvancedSoleusLeftRaw from '@/assets/anatomy/female/back/advanced/soleus-left.svg?raw';
import femaleBackAdvancedSoleusRightRaw from '@/assets/anatomy/female/back/advanced/soleus-right.svg?raw';
import femaleBackAdvancedGastrocnemiusLeftRaw from '@/assets/anatomy/female/back/advanced/gastrocnemius-left.svg?raw';
import femaleBackAdvancedGastrocnemiusRightRaw from '@/assets/anatomy/female/back/advanced/gastrocnemius-right.svg?raw';
import femaleBackAdvancedFeetLeftRaw from '@/assets/anatomy/female/back/advanced/feet-left.svg?raw';
import femaleBackAdvancedFeetRightRaw from '@/assets/anatomy/female/back/advanced/feet-right.svg?raw';
import maleFrontAdvancedBase from '@/assets/anatomy/male/front/advanced/base-transparent.png';
import maleFrontAdvancedNeckRaw from '@/assets/anatomy/male/front/advanced/neck.svg?raw';
import maleFrontAdvancedUpperTrapeziusLeftRaw from '@/assets/anatomy/male/front/advanced/upper-trapezius-left.svg?raw';
import maleFrontAdvancedUpperTrapeziusRightRaw from '@/assets/anatomy/male/front/advanced/upper-trapezius-right.svg?raw';
import maleFrontAdvancedAnteriorDeltoidLeftRaw from '@/assets/anatomy/male/front/advanced/anterior-deltoid-left.svg?raw';
import maleFrontAdvancedAnteriorDeltoidRightRaw from '@/assets/anatomy/male/front/advanced/anterior-deltoid-right.svg?raw';
import maleFrontAdvancedLateralDeltoidLeftRaw from '@/assets/anatomy/male/front/advanced/lateral-deltoid-left.svg?raw';
import maleFrontAdvancedLateralDeltoidRightRaw from '@/assets/anatomy/male/front/advanced/lateral-deltoid-right.svg?raw';
import maleFrontAdvancedUpperPectoralisLeftRaw from '@/assets/anatomy/male/front/advanced/upper-pectoralis-left.svg?raw';
import maleFrontAdvancedUpperPectoralisRightRaw from '@/assets/anatomy/male/front/advanced/upper-pectoralis-right.svg?raw';
import maleFrontAdvancedMidLowerPectoralisLeftRaw from '@/assets/anatomy/male/front/advanced/mid-lower-pectoralis-left.svg?raw';
import maleFrontAdvancedMidLowerPectoralisRightRaw from '@/assets/anatomy/male/front/advanced/mid-lower-pectoralis-right.svg?raw';
import maleFrontAdvancedLongHeadBicepLeftRaw from '@/assets/anatomy/male/front/advanced/long-head-bicep-left.svg?raw';
import maleFrontAdvancedLongHeadBicepRightRaw from '@/assets/anatomy/male/front/advanced/long-head-bicep-right.svg?raw';
import maleFrontAdvancedShortHeadBicepLeftRaw from '@/assets/anatomy/male/front/advanced/short-head-bicep-left.svg?raw';
import maleFrontAdvancedShortHeadBicepRightRaw from '@/assets/anatomy/male/front/advanced/short-head-bicep-right.svg?raw';
import maleFrontAdvancedWristExtensorsLeftRaw from '@/assets/anatomy/male/front/advanced/wrist-extensors-left.svg?raw';
import maleFrontAdvancedWristExtensorsRightRaw from '@/assets/anatomy/male/front/advanced/wrist-extensors-right.svg?raw';
import maleFrontAdvancedWristFlexorsLeftRaw from '@/assets/anatomy/male/front/advanced/wrist-flexors-left.svg?raw';
import maleFrontAdvancedWristFlexorsRightRaw from '@/assets/anatomy/male/front/advanced/wrist-flexors-right.svg?raw';
import maleFrontAdvancedHandsLeftRaw from '@/assets/anatomy/male/front/advanced/hands-left.svg?raw';
import maleFrontAdvancedHandsRightRaw from '@/assets/anatomy/male/front/advanced/hands-right.svg?raw';
import maleFrontAdvancedAbsUpRaw from '@/assets/anatomy/male/front/advanced/abs-up.svg?raw';
import maleFrontAdvancedAbsDownRaw from '@/assets/anatomy/male/front/advanced/abs-down.svg?raw';
import maleFrontAdvancedObliquesLeftRaw from '@/assets/anatomy/male/front/advanced/obliques-left.svg?raw';
import maleFrontAdvancedObliquesRightRaw from '@/assets/anatomy/male/front/advanced/obliques-right.svg?raw';
import maleFrontAdvancedRectusFemorisLeftRaw from '@/assets/anatomy/male/front/advanced/rectus-femoris-left.svg?raw';
import maleFrontAdvancedRectusFemorisRightRaw from '@/assets/anatomy/male/front/advanced/rectus-femoris-right.svg?raw';
import maleFrontAdvancedOuterQuadricepLeftRaw from '@/assets/anatomy/male/front/advanced/outer-quadricep-left.svg?raw';
import maleFrontAdvancedOuterQuadricepRightRaw from '@/assets/anatomy/male/front/advanced/outer-quadricep-right.svg?raw';
import maleFrontAdvancedInnerQuadricepLeftRaw from '@/assets/anatomy/male/front/advanced/inner-quadricep-left.svg?raw';
import maleFrontAdvancedInnerQuadricepRightRaw from '@/assets/anatomy/male/front/advanced/inner-quadricep-right.svg?raw';
import maleFrontAdvancedInnerThighLeftRaw from '@/assets/anatomy/male/front/advanced/inner-thigh-left.svg?raw';
import maleFrontAdvancedInnerThighRightRaw from '@/assets/anatomy/male/front/advanced/inner-thigh-right.svg?raw';
import maleFrontAdvancedGastrocnemiusLeftRaw from '@/assets/anatomy/male/front/advanced/gastrocnemius-left.svg?raw';
import maleFrontAdvancedGastrocnemiusRightRaw from '@/assets/anatomy/male/front/advanced/gastrocnemius-right.svg?raw';
import maleFrontAdvancedSoleusLeftRaw from '@/assets/anatomy/male/front/advanced/soleus-left.svg?raw';
import maleFrontAdvancedSoleusRightRaw from '@/assets/anatomy/male/front/advanced/soleus-right.svg?raw';
import maleFrontAdvancedTibialisLeftRaw from '@/assets/anatomy/male/front/advanced/tibialis-left.svg?raw';
import maleFrontAdvancedTibialisRightRaw from '@/assets/anatomy/male/front/advanced/tibialis-right.svg?raw';
import maleFrontAdvancedFeetLeftRaw from '@/assets/anatomy/male/front/advanced/feet-left.svg?raw';
import maleFrontAdvancedFeetRightRaw from '@/assets/anatomy/male/front/advanced/feet-right.svg?raw';
import maleFrontAdvancedGroinRaw from '@/assets/anatomy/male/front/advanced/groin.svg?raw';
import maleBackAdvancedBase from '@/assets/anatomy/male/back/advanced/base-transparent.png';
import maleBackAdvancedNeckRaw from '@/assets/anatomy/male/back/advanced/neck.svg?raw';
import maleBackAdvancedUpperTrapeziusRaw from '@/assets/anatomy/male/back/advanced/upper-trapezius.svg?raw';
import maleBackAdvancedTrapsMiddleRaw from '@/assets/anatomy/male/back/advanced/traps-middle.svg?raw';
import maleBackAdvancedLowerTrapeziusRaw from '@/assets/anatomy/male/back/advanced/lower-trapezius.svg?raw';
import maleBackAdvancedLateralDeltoidLeftRaw from '@/assets/anatomy/male/back/advanced/lateral-deltoid-left.svg?raw';
import maleBackAdvancedLateralDeltoidRightRaw from '@/assets/anatomy/male/back/advanced/lateral-deltoid-right.svg?raw';
import maleBackAdvancedPosteriorDeltoidLeftRaw from '@/assets/anatomy/male/back/advanced/posterior-deltoid-left.svg?raw';
import maleBackAdvancedPosteriorDeltoidRightRaw from '@/assets/anatomy/male/back/advanced/posterior-deltoid-right.svg?raw';
import maleBackAdvancedLongHeadTricepsLeftRaw from '@/assets/anatomy/male/back/advanced/long-head-triceps-left.svg?raw';
import maleBackAdvancedLongHeadTricepsRightRaw from '@/assets/anatomy/male/back/advanced/long-head-triceps-right.svg?raw';
import maleBackAdvancedLateralHeadTricepsLeftRaw from '@/assets/anatomy/male/back/advanced/lateral-head-triceps-left.svg?raw';
import maleBackAdvancedLateralHeadTricepsRightRaw from '@/assets/anatomy/male/back/advanced/lateral-head-triceps-right.svg?raw';
import maleBackAdvancedMedialHeadTricepsLeftRaw from '@/assets/anatomy/male/back/advanced/medial-head-triceps-left.svg?raw';
import maleBackAdvancedMedialHeadTricepsRightRaw from '@/assets/anatomy/male/back/advanced/medial-head-triceps-right.svg?raw';
import maleBackAdvancedWristExtensorsLeftRaw from '@/assets/anatomy/male/back/advanced/wrist-extensors-left.svg?raw';
import maleBackAdvancedWristExtensorsRightRaw from '@/assets/anatomy/male/back/advanced/wrist-extensors-right.svg?raw';
import maleBackAdvancedWristFlexorsLeftRaw from '@/assets/anatomy/male/back/advanced/wrist-flexors-left.svg?raw';
import maleBackAdvancedWristFlexorsRightRaw from '@/assets/anatomy/male/back/advanced/wrist-flexors-right.svg?raw';
import maleBackAdvancedHandsLeftRaw from '@/assets/anatomy/male/back/advanced/hands-left.svg?raw';
import maleBackAdvancedHandsRightRaw from '@/assets/anatomy/male/back/advanced/hands-right.svg?raw';
import maleBackAdvancedLatsLeftRaw from '@/assets/anatomy/male/back/advanced/lats-left.svg?raw';
import maleBackAdvancedLatsRightRaw from '@/assets/anatomy/male/back/advanced/lats-right.svg?raw';
import maleBackAdvancedLowerBackRaw from '@/assets/anatomy/male/back/advanced/lower-back.svg?raw';
import maleBackAdvancedGluteusMediusLeftRaw from '@/assets/anatomy/male/back/advanced/gluteus-medius-left.svg?raw';
import maleBackAdvancedGluteusMediusRightRaw from '@/assets/anatomy/male/back/advanced/gluteus-medius-right.svg?raw';
import maleBackAdvancedGluteusMaximusLeftRaw from '@/assets/anatomy/male/back/advanced/gluteus-maximus-left.svg?raw';
import maleBackAdvancedGluteusMaximusRightRaw from '@/assets/anatomy/male/back/advanced/gluteus-maximus-right.svg?raw';
import maleBackAdvancedInnerThighLeftRaw from '@/assets/anatomy/male/back/advanced/inner-thigh-left.svg?raw';
import maleBackAdvancedInnerThighRightRaw from '@/assets/anatomy/male/back/advanced/inner-thigh-right.svg?raw';
import maleBackAdvancedMedialHamstringsLeftRaw from '@/assets/anatomy/male/back/advanced/medial-hamstrings-left.svg?raw';
import maleBackAdvancedMedialHamstringsRightRaw from '@/assets/anatomy/male/back/advanced/medial-hamstrings-right.svg?raw';
import maleBackAdvancedLateralHamstringsLeftRaw from '@/assets/anatomy/male/back/advanced/lateral-hamstrings-left.svg?raw';
import maleBackAdvancedLateralHamstringsRightRaw from '@/assets/anatomy/male/back/advanced/lateral-hamstrings-right.svg?raw';
import maleBackAdvancedSoleusLeftRaw from '@/assets/anatomy/male/back/advanced/soleus-left.svg?raw';
import maleBackAdvancedSoleusRightRaw from '@/assets/anatomy/male/back/advanced/soleus-right.svg?raw';
import maleBackAdvancedGastrocnemiusLeftRaw from '@/assets/anatomy/male/back/advanced/gastrocnemius-left.svg?raw';
import maleBackAdvancedGastrocnemiusRightRaw from '@/assets/anatomy/male/back/advanced/gastrocnemius-right.svg?raw';
import maleBackAdvancedFeetLeftRaw from '@/assets/anatomy/male/back/advanced/feet-left.svg?raw';
import maleBackAdvancedFeetRightRaw from '@/assets/anatomy/male/back/advanced/feet-right.svg?raw';
import maleFrontBase from '@/assets/anatomy/male/front/normal/base-front-transparent.png';
import maleFrontAbsRaw from '@/assets/anatomy/male/front/normal/abs.svg?raw';
import maleFrontBicepsLeftRaw from '@/assets/anatomy/male/front/normal/biceps-left.svg?raw';
import maleFrontBicepsRightRaw from '@/assets/anatomy/male/front/normal/biceps-right.svg?raw';
import maleFrontForearmLeftRaw from '@/assets/anatomy/male/front/normal/forearm-left.svg?raw';
import maleFrontForearmRightRaw from '@/assets/anatomy/male/front/normal/forearm-right.svg?raw';
import maleFrontChestLeftRaw from '@/assets/anatomy/male/front/normal/chest-left.svg?raw';
import maleFrontChestRightRaw from '@/assets/anatomy/male/front/normal/chest-right.svg?raw';
import maleFrontObliquesLeftRaw from '@/assets/anatomy/male/front/normal/obliques-left.svg?raw';
import maleFrontObliquesRightRaw from '@/assets/anatomy/male/front/normal/obliques-right.svg?raw';
import maleFrontQuadLeftRaw from '@/assets/anatomy/male/front/normal/quad-left.svg?raw';
import maleFrontQuadRightRaw from '@/assets/anatomy/male/front/normal/quad-right.svg?raw';
import maleFrontCalfLeftRaw from '@/assets/anatomy/male/front/normal/calf-left.svg?raw';
import maleFrontCalfRightRaw from '@/assets/anatomy/male/front/normal/calf-right.svg?raw';
import maleFrontTrapsLeftRaw from '@/assets/anatomy/male/front/normal/traps-left.svg?raw';
import maleFrontTrapsRightRaw from '@/assets/anatomy/male/front/normal/traps-right.svg?raw';
import maleFrontRearShouldersLeftRaw from '@/assets/anatomy/male/front/normal/rear-shoulders-left-front.svg?raw';
import maleFrontRearShouldersRightRaw from '@/assets/anatomy/male/front/normal/rear-shoulders-right-front.svg?raw';
import maleFrontHandsLeftRaw from '@/assets/anatomy/male/front/normal/hands-left-front.svg?raw';
import maleFrontHandsRightRaw from '@/assets/anatomy/male/front/normal/hands-right-front.svg?raw';
import maleBackBase from '@/assets/anatomy/male/back/normal/base-transparent.png';
import maleBackTrapsTopRaw from '@/assets/anatomy/male/back/normal/traps-top.svg?raw';
import maleBackTrapsMiddleRaw from '@/assets/anatomy/male/back/normal/traps-middle.svg?raw';
import maleBackRearShoulderLeftRaw from '@/assets/anatomy/male/back/normal/rear-shoulders-left.svg?raw';
import maleBackRearShoulderRightRaw from '@/assets/anatomy/male/back/normal/rear-shoulders-right.svg?raw';
import maleBackLatsLeftRaw from '@/assets/anatomy/male/back/normal/lats-left.svg?raw';
import maleBackLatsRightRaw from '@/assets/anatomy/male/back/normal/lats-right.svg?raw';
import maleBackLowerBackRaw from '@/assets/anatomy/male/back/normal/lower-back.svg?raw';
import maleBackTricepsLeftRaw from '@/assets/anatomy/male/back/normal/triceps-left.svg?raw';
import maleBackTricepsRightRaw from '@/assets/anatomy/male/back/normal/triceps-right.svg?raw';
import maleBackForearmsLeftRaw from '@/assets/anatomy/male/back/normal/forearms-left.svg?raw';
import maleBackForearmsRightRaw from '@/assets/anatomy/male/back/normal/forearms-right.svg?raw';
import maleBackHandsLeftRaw from '@/assets/anatomy/male/back/normal/hands-left.svg?raw';
import maleBackHandsRightRaw from '@/assets/anatomy/male/back/normal/hands-right.svg?raw';
import maleBackGlutesLeftRaw from '@/assets/anatomy/male/back/normal/glutes-left.svg?raw';
import maleBackGlutesRightRaw from '@/assets/anatomy/male/back/normal/glutes-right.svg?raw';
import maleBackHamstringsLeftRaw from '@/assets/anatomy/male/back/normal/hamstrings-left.svg?raw';
import maleBackHamstringsRightRaw from '@/assets/anatomy/male/back/normal/hamstrings-right.svg?raw';
import maleBackCalvesLeftRaw from '@/assets/anatomy/male/back/normal/calf-left.svg?raw';
import maleBackCalvesRightRaw from '@/assets/anatomy/male/back/normal/calf-right.svg?raw';
import femaleBackBase from '@/assets/anatomy/female/back/normal/base-transparent.png';
import femaleBackTrapsTopRaw from '@/assets/anatomy/female/back/normal/traps-top.svg?raw';
import femaleBackTrapsMiddleRaw from '@/assets/anatomy/female/back/normal/traps-middle.svg?raw';
import femaleBackRearShoulderLeftRaw from '@/assets/anatomy/female/back/normal/rear-shoulders-left.svg?raw';
import femaleBackRearShoulderRightRaw from '@/assets/anatomy/female/back/normal/rear-shoulders-right.svg?raw';
import femaleBackLatsLeftRaw from '@/assets/anatomy/female/back/normal/lats-left.svg?raw';
import femaleBackLatsRightRaw from '@/assets/anatomy/female/back/normal/lats-right.svg?raw';
import femaleBackLowerBackRaw from '@/assets/anatomy/female/back/normal/lower-back.svg?raw';
import femaleBackTricepsLeftRaw from '@/assets/anatomy/female/back/normal/triceps-left.svg?raw';
import femaleBackTricepsRightRaw from '@/assets/anatomy/female/back/normal/triceps-right.svg?raw';
import femaleBackForearmsLeftRaw from '@/assets/anatomy/female/back/normal/forearms-left.svg?raw';
import femaleBackForearmsRightRaw from '@/assets/anatomy/female/back/normal/forearms-right.svg?raw';
import femaleBackHandsLeftRaw from '@/assets/anatomy/female/back/normal/hands-left.svg?raw';
import femaleBackHandsRightRaw from '@/assets/anatomy/female/back/normal/hands-right.svg?raw';
import femaleBackGlutesLeftRaw from '@/assets/anatomy/female/back/normal/glutes-left.svg?raw';
import femaleBackGlutesRightRaw from '@/assets/anatomy/female/back/normal/glutes-right.svg?raw';
import femaleBackHamstringsLeftRaw from '@/assets/anatomy/female/back/normal/hamstrings-left.svg?raw';
import femaleBackHamstringsRightRaw from '@/assets/anatomy/female/back/normal/hamstrings-right.svg?raw';
import femaleBackCalvesLeftRaw from '@/assets/anatomy/female/back/normal/calves-left.svg?raw';
import femaleBackCalvesRightRaw from '@/assets/anatomy/female/back/normal/calves-right.svg?raw';

interface AnatomyBodyProps {
  selectedMuscles: string[];
  onMuscleToggle: (muscleId: string) => void;
  muscleNames: Record<string, string>;
}

type BodyView = 'front' | 'back';
type BodyGender = 'male' | 'female';
type BodyLevel = 'normal' | 'advanced';

interface ParsedSvgLayer {
  pathDs: string[];
  sourceWidth: number;
  sourceHeight: number;
  sourceOffsetX: number;
  sourceOffsetY: number;
}

interface FemaleNormalLayer {
  id: string;
  svgRaw: string;
  x: number;
  y: number;
  width: number;
  height: number;
  muscleId: string;
  activeMuscles?: string[];
}

type ParsedFemaleNormalLayer = FemaleNormalLayer & ParsedSvgLayer;

interface MuscleLabel {
  en: string;
  ar: string;
}

const FEMALE_FRONT_CANVAS = {
  width: 542,
  height: 806,
};

const FEMALE_FRONT_ADVANCED_CANVAS = {
  width: 562,
  height: 799,
};

const MALE_FRONT_CANVAS = {
  width: 535,
  height: 805,
};

const MALE_FRONT_ADVANCED_CANVAS = {
  width: 512,
  height: 805,
};

const MALE_BACK_CANVAS = {
  width: 622,
  height: 802,
};

const MALE_BACK_ADVANCED_CANVAS = {
  width: 586,
  height: 808,
};

const FEMALE_BACK_CANVAS = {
  width: 631,
  height: 807,
};

const FEMALE_BACK_ADVANCED_CANVAS = {
  width: 620,
  height: 806,
};

interface PathBounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

const commandRegex = /[AaCcHhLlMmQqSsTtVvZz]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?/g;
const isCommandToken = (token: string) => /^[AaCcHhLlMmQqSsTtVvZz]$/.test(token);

const getPathBounds = (pathD: string): PathBounds | null => {
  const tokens = pathD.match(commandRegex);
  if (!tokens || tokens.length === 0) return null;

  let i = 0;
  let command: string | null = null;
  let x = 0;
  let y = 0;
  let startX = 0;
  let startY = 0;
  const points: Array<{ x: number; y: number }> = [];

  const readNumber = (): number => {
    const value = Number(tokens[i]);
    i += 1;
    return value;
  };

  while (i < tokens.length) {
    const token = tokens[i];
    if (isCommandToken(token)) {
      command = token;
      i += 1;
      if (command === 'Z' || command === 'z') {
        x = startX;
        y = startY;
        points.push({ x, y });
        continue;
      }
    }

    if (!command) break;

    if (command === 'M' || command === 'm') {
      let firstPoint = true;
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const nextX = readNumber();
        const nextY = readNumber();
        if (command === 'm') {
          x += nextX;
          y += nextY;
        } else {
          x = nextX;
          y = nextY;
        }
        points.push({ x, y });
        if (firstPoint) {
          startX = x;
          startY = y;
          firstPoint = false;
        }
        command = command === 'm' ? 'l' : 'L';
      }
      continue;
    }

    if (command === 'L' || command === 'l') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const nextX = readNumber();
        const nextY = readNumber();
        if (command === 'l') {
          x += nextX;
          y += nextY;
        } else {
          x = nextX;
          y = nextY;
        }
        points.push({ x, y });
      }
      continue;
    }

    if (command === 'H' || command === 'h') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const nextX = readNumber();
        x = command === 'h' ? x + nextX : nextX;
        points.push({ x, y });
      }
      continue;
    }

    if (command === 'V' || command === 'v') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const nextY = readNumber();
        y = command === 'v' ? y + nextY : nextY;
        points.push({ x, y });
      }
      continue;
    }

    if (command === 'C' || command === 'c') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const x1 = readNumber();
        const y1 = readNumber();
        const x2 = readNumber();
        const y2 = readNumber();
        const x3 = readNumber();
        const y3 = readNumber();

        if (command === 'c') {
          points.push({ x: x + x1, y: y + y1 }, { x: x + x2, y: y + y2 }, { x: x + x3, y: y + y3 });
          x += x3;
          y += y3;
        } else {
          points.push({ x: x1, y: y1 }, { x: x2, y: y2 }, { x: x3, y: y3 });
          x = x3;
          y = y3;
        }
      }
      continue;
    }

    if (command === 'S' || command === 's') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const x2 = readNumber();
        const y2 = readNumber();
        const x3 = readNumber();
        const y3 = readNumber();
        if (command === 's') {
          points.push({ x: x + x2, y: y + y2 }, { x: x + x3, y: y + y3 });
          x += x3;
          y += y3;
        } else {
          points.push({ x: x2, y: y2 }, { x: x3, y: y3 });
          x = x3;
          y = y3;
        }
      }
      continue;
    }

    if (command === 'Q' || command === 'q') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const x1 = readNumber();
        const y1 = readNumber();
        const x2 = readNumber();
        const y2 = readNumber();
        if (command === 'q') {
          points.push({ x: x + x1, y: y + y1 }, { x: x + x2, y: y + y2 });
          x += x2;
          y += y2;
        } else {
          points.push({ x: x1, y: y1 }, { x: x2, y: y2 });
          x = x2;
          y = y2;
        }
      }
      continue;
    }

    if (command === 'T' || command === 't') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const x2 = readNumber();
        const y2 = readNumber();
        if (command === 't') {
          x += x2;
          y += y2;
        } else {
          x = x2;
          y = y2;
        }
        points.push({ x, y });
      }
      continue;
    }

    if (command === 'A' || command === 'a') {
      while (i < tokens.length && !isCommandToken(tokens[i])) {
        const rx = readNumber();
        const ry = readNumber();
        readNumber(); // x-axis rotation
        readNumber(); // large-arc flag
        readNumber(); // sweep flag
        const x2 = readNumber();
        const y2 = readNumber();
        if (command === 'a') {
          x += x2;
          y += y2;
        } else {
          x = x2;
          y = y2;
        }
        points.push({ x, y }, { x: x + rx, y: y + ry }, { x: x - rx, y: y - ry });
      }
      continue;
    }
  }

  if (points.length === 0) return null;

  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  return {
    minX: Math.min(...xs),
    minY: Math.min(...ys),
    maxX: Math.max(...xs),
    maxY: Math.max(...ys),
  };
};

const parseSvgLayer = (svgRaw: string): ParsedSvgLayer => {
  const viewBoxMatch = svgRaw.match(/viewBox="[^"]*?([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"/i);
  const svgFillMatch = svgRaw.match(/<svg[^>]*\sfill="([^"]+)"/i);
  const svgDefaultFill = (svgFillMatch?.[1] ?? '').trim().toLowerCase();
  const pathMatches = [...svgRaw.matchAll(/<path\b([^>]*)>/gi)];

  const sourceWidth = viewBoxMatch ? Number(viewBoxMatch[3]) : 1;
  const sourceHeight = viewBoxMatch ? Number(viewBoxMatch[4]) : 1;
  const allPathDs: string[] = [];
  const fillPathDs: string[] = [];

  pathMatches.forEach((match) => {
    const attrs = match[1];
    const dMatch = attrs.match(/\sd="([^"]+)"/i);
    if (!dMatch) return;

    const pathD = dMatch[1];
    allPathDs.push(pathD);

    const pathFillMatch = attrs.match(/\sfill="([^"]+)"/i);
    const pathFill = (pathFillMatch?.[1] ?? svgDefaultFill).trim().toLowerCase();
    if (pathFill && pathFill !== 'none' && pathFill !== 'transparent') {
      fillPathDs.push(pathD);
    }
  });

  const pathDs = fillPathDs.length > 0
    ? fillPathDs
    : allPathDs.length > 0
      ? allPathDs
      : [`M0 0 H${sourceWidth} V${sourceHeight} H0 Z`];

  const bounds = pathDs
    .map((pathD) => getPathBounds(pathD))
    .filter((value): value is PathBounds => Boolean(value))
    .reduce<PathBounds | null>((acc, value) => {
      if (!acc) return value;
      return {
        minX: Math.min(acc.minX, value.minX),
        minY: Math.min(acc.minY, value.minY),
        maxX: Math.max(acc.maxX, value.maxX),
        maxY: Math.max(acc.maxY, value.maxY),
      };
    }, null);

  if (!bounds) {
    return { pathDs, sourceWidth, sourceHeight, sourceOffsetX: 0, sourceOffsetY: 0 };
  }

  const boundsWidth = bounds.maxX - bounds.minX;
  const boundsHeight = bounds.maxY - bounds.minY;
  const shouldNormalize =
    boundsWidth > 0 &&
    boundsHeight > 0 &&
    (bounds.minX > 1 || bounds.minY > 1 || Math.abs(sourceWidth - boundsWidth) > 1 || Math.abs(sourceHeight - boundsHeight) > 1);

  return {
    pathDs,
    sourceWidth: shouldNormalize ? boundsWidth : sourceWidth,
    sourceHeight: shouldNormalize ? boundsHeight : sourceHeight,
    sourceOffsetX: shouldNormalize ? bounds.minX : 0,
    sourceOffsetY: shouldNormalize ? bounds.minY : 0,
  };
};

const femaleFrontNormalLayers: FemaleNormalLayer[] = [
  { id: 'right_traps', svgRaw: femaleFrontNeck2Raw, x: 221, y: 141, width: 26, height: 16, muscleId: 'traps' },
  { id: 'Left_traps', svgRaw: femaleFrontNeck1Raw, x: 299, y: 141, width: 26, height: 16, muscleId: 'traps' },
  { id: 'right_front_shoulders', svgRaw: femaleFrontShoulderRightRaw, x: 169.19, y: 159.5, width: 56.5, height: 54, muscleId: 'rear_delts' },
  { id: 'left_front_shoulders', svgRaw: femaleFrontShoulderLeftRaw, x: 321, y: 159.5, width: 56.5, height: 54, muscleId: 'rear_delts' },
  { id: 'chest_right', svgRaw: femaleFrontChestRightRaw, x: 192, y: 160, width: 79.5, height: 65.5, muscleId: 'chest' },
  { id: 'chest_left', svgRaw: femaleFrontChestLeftRaw, x: 276, y: 160, width: 79.5, height: 65.5, muscleId: 'chest' },
  { id: 'right_obliques', svgRaw: femaleFrontAbsSideRightRaw, x: 207, y: 209, width: 33.86, height: 129, muscleId: 'obliques' },
  { id: 'left_obliques', svgRaw: femaleFrontAbsSideLeftRaw, x: 308, y: 209, width: 33.86, height: 129, muscleId: 'obliques' },
  { id: 'Abs', svgRaw: femaleFrontAbsRaw, x: 241.28, y: 225.5, width: 63.22, height: 162.1, muscleId: 'abs' },
  { id: 'biceps_right', svgRaw: femaleFrontBicepsRightRaw, x: 145, y: 203, width: 57.5, height: 70, muscleId: 'biceps' },
  { id: 'biceps_left', svgRaw: femaleFrontBicepsLeftRaw, x: 343, y: 203, width: 57.5, height: 70, muscleId: 'biceps' },
  { id: 'right_forearms', svgRaw: femaleFrontForearmRightRaw, x: 89, y: 250, width: 76.5, height: 88.33, muscleId: 'forearms' },
  { id: 'left_forearms', svgRaw: femaleFrontForearmLeftRaw, x: 381, y: 250, width: 76.5, height: 88.33, muscleId: 'forearms' },
  { id: 'hands_r_front_normal', svgRaw: femaleFrontHandsRightRaw, x: 59, y: 329, width: 38, height: 82, muscleId: 'hands' },
  { id: 'hands_l_front_normal', svgRaw: femaleFrontHandsLeftRaw, x: 449, y: 329, width: 38, height: 82, muscleId: 'hands' },
  { id: 'right_quads', svgRaw: femaleFrontQuadRightRaw, x: 188, y: 341, width: 83, height: 233, muscleId: 'quads', activeMuscles: ['quads', 'adductors'] },
  { id: 'left_quads', svgRaw: femaleFrontQuadLeftRaw, x: 276.5, y: 341, width: 83, height: 233, muscleId: 'quads', activeMuscles: ['quads', 'adductors'] },
  { id: 'right_calves', svgRaw: femaleFrontShinRightRaw, x: 161.4, y: 588, width: 64.6, height: 209.33, muscleId: 'calves' },
  { id: 'left_calves', svgRaw: femaleFrontShinLeftRaw, x: 320.5, y: 588, width: 64.6, height: 209.33, muscleId: 'calves' },
];

const parsedFemaleFrontNormalLayers: ParsedFemaleNormalLayer[] = femaleFrontNormalLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

const femaleFrontAdvancedLayers: FemaleNormalLayer[] = [
  { id: 'neck-center', svgRaw: femaleFrontAdvancedNeckCenterRaw, x: 252.14, y: 112.42, width: 49.32, height: 50.08, muscleId: 'neck' },
  { id: 'upper-trapezius-left-front-female', svgRaw: femaleFrontAdvancedNeckLeftRaw, x: 303.5, y: 136.41, width: 25.65, height: 16, muscleId: 'upper_trapezius' },
  { id: 'upper-trapezius-right-front-female', svgRaw: femaleFrontAdvancedNeckRightRaw, x: 224.15, y: 136.141, width: 26, height: 16, muscleId: 'upper_trapezius' },
  { id: 'anterior-deltoid-left', svgRaw: femaleFrontAdvancedAnteriorDeltoidLeftRaw, x: 326, y: 155.63, width: 39.96, height: 40.02, muscleId: 'anterior_deltoid' },
  { id: 'anterior-deltoid-right', svgRaw: femaleFrontAdvancedAnteriorDeltoidRightRaw, x: 188.5, y: 155.6, width: 39.96, height: 40.02, muscleId: 'anterior_deltoid' },
  { id: 'lateral-deltoid-left', svgRaw: femaleFrontAdvancedLateralDeltoidLeftRaw, x: 342, y: 153.6, width: 43.78, height: 57.39, muscleId: 'lateral_deltoid' },
  { id: 'lateral-deltoid-right', svgRaw: femaleFrontAdvancedLateralDeltoidRightRaw, x: 168.5, y: 153.6, width: 43.78, height: 57.39, muscleId: 'lateral_deltoid' },
  { id: 'upper-pectoralis-left', svgRaw: femaleFrontAdvancedUpperPectoralisLeftRaw, x: 291, y: 155, width: 70, height: 39, muscleId: 'upper_pectoralis' },
  { id: 'upper-pectoralis-right', svgRaw: femaleFrontAdvancedUpperPectoralisRightRaw, x: 193.5, y: 155, width: 70, height: 39, muscleId: 'upper_pectoralis' },
  { id: 'mid-lower-pectoralis-left', svgRaw: femaleFrontAdvancedMidLowerPectoralisLeftRaw, x: 279, y: 157.5, width: 74.5, height: 63, muscleId: 'mid_lower_pectoralis' },
  { id: 'mid-lower-pectoralis-right', svgRaw: femaleFrontAdvancedMidLowerPectoralisRightRaw, x: 200.5, y: 157.5, width: 74.5, height: 63, muscleId: 'mid_lower_pectoralis' },
  { id: 'long-head-bicep-left', svgRaw: femaleFrontAdvancedLongHeadBicepLeftRaw, x: 369, y: 201.3, width: 39.5, height: 67.19, muscleId: 'long_head_bicep' },
  { id: 'long-head-bicep-right', svgRaw: femaleFrontAdvancedLongHeadBicepRightRaw, x: 145.5, y: 201.3, width: 39.5, height: 67.19, muscleId: 'long_head_bicep' },
  { id: 'short-head-bicep-left', svgRaw: femaleFrontAdvancedShortHeadBicepLeftRaw, x: 348.5, y: 199.05, width: 51.72, height: 68.07, muscleId: 'short_head_bicep' },
  { id: 'short-head-bicep-right', svgRaw: femaleFrontAdvancedShortHeadBicepRightRaw, x: 154, y: 199.05, width: 51.72, height: 68.07, muscleId: 'short_head_bicep' },
  { id: 'wrist-extensors-left', svgRaw: femaleFrontAdvancedWristExtensorsLeftRaw, x: 409, y: 246, width: 58.5, height: 83, muscleId: 'wrist_extensors' },
  { id: 'wrist-extensors-right', svgRaw: femaleFrontAdvancedWristExtensorsRightRaw, x: 87.5, y: 246, width: 58.5, height: 83, muscleId: 'wrist_extensors' },
  { id: 'wrist-flexors-left', svgRaw: femaleFrontAdvancedWristFlexorsLeftRaw, x: 389, y: 266.5, width: 73.5, height: 66, muscleId: 'wrist_flexors' },
  { id: 'wrist-flexors-right', svgRaw: femaleFrontAdvancedWristFlexorsRightRaw, x: 91, y: 266.5, width: 73.5, height: 66, muscleId: 'wrist_flexors' },
  { id: 'hands-left', svgRaw: femaleFrontAdvancedHandsLeftRaw, x: 458, y: 324, width: 38, height: 82, muscleId: 'hands' },
  { id: 'hands-right', svgRaw: femaleFrontAdvancedHandsRightRaw, x: 57, y: 324, width: 38, height: 82, muscleId: 'hands' },
  { id: 'abs-up', svgRaw: femaleFrontAdvancedAbsUpRaw, x: 245.5, y: 220.5, width: 63.06, height: 56.5, muscleId: 'abs_up' },
  { id: 'abs-down', svgRaw: femaleFrontAdvancedAbsDownRaw, x: 248, y: 281, width: 58, height: 102, muscleId: 'abs_down' },
  { id: 'side-abs-left', svgRaw: femaleFrontAdvancedSideAbsLeftRaw, x: 311, y: 205, width: 35, height: 129, muscleId: 'obliques' },
  { id: 'side-abs-right', svgRaw: femaleFrontAdvancedSideAbsRightRaw, x: 208, y: 205, width: 35, height: 129, muscleId: 'obliques' },
  { id: 'rectus-femoris-left', svgRaw: femaleFrontAdvancedRectusFemorisLeftRaw, x: 315.5, y: 347, width: 28.5, height: 222, muscleId: 'rectus_femoris' },
  { id: 'rectus-femoris-right', svgRaw: femaleFrontAdvancedRectusFemorisRightRaw, x: 210.1, y: 347, width: 28.5, height: 222, muscleId: 'rectus_femoris' },
  { id: 'outer-quadricep-left', svgRaw: femaleFrontAdvancedOuterQuadricepLeftRaw, x: 339, y: 340, width: 24.36, height: 207, muscleId: 'outer_quadricep' },
  { id: 'outer-quadricep-right', svgRaw: femaleFrontAdvancedOuterQuadricepRightRaw, x: 191.06, y: 339.94, width: 24.36, height: 207, muscleId: 'outer_quadricep' },
  { id: 'inner-quadricep-left', svgRaw: femaleFrontAdvancedInnerQuadricepLeftRaw, x: 305, y: 470, width: 11.61, height: 82, muscleId: 'inner_quadricep' },
  { id: 'inner-quadricep-right', svgRaw: femaleFrontAdvancedInnerQuadricepRightRaw, x: 237.3, y: 470, width: 11.61, height: 81.5, muscleId: 'inner_quadricep' },
  { id: 'inner-thigh-left', svgRaw: femaleFrontAdvancedInnerThighLeftRaw, x: 279, y: 336.5, width: 67, height: 155, muscleId: 'inner_thigh' },
  { id: 'inner-thigh-right', svgRaw: femaleFrontAdvancedInnerThighRightRaw, x: 208, y: 336.5, width: 67, height: 155, muscleId: 'inner_thigh' },
  { id: 'gastrocnemius-left', svgRaw: femaleFrontAdvancedGastrocnemiusLeftRaw, x: 325, y: 599.5, width: 21.5, height: 135, muscleId: 'gastrocnemius' },
  { id: 'gastrocnemius-right', svgRaw: femaleFrontAdvancedGastrocnemiusRightRaw, x: 207, y: 599.5, width: 21.5, height: 135, muscleId: 'gastrocnemius' },
  { id: 'soleus-left', svgRaw: femaleFrontAdvancedSoleusLeftRaw, x: 359, y: 584, width: 10.72, height: 148, muscleId: 'soleus' },
  { id: 'soleus-right', svgRaw: femaleFrontAdvancedSoleusRightRaw, x: 184.28, y: 584, width: 10.72, height: 148, muscleId: 'soleus' },
  { id: 'tibialis-left', svgRaw: femaleFrontAdvancedTibialisLeftRaw, x: 340.9, y: 602, width: 15.5, height: 133, muscleId: 'tibialis' },
  { id: 'tibialis-right', svgRaw: femaleFrontAdvancedTibialisRightRaw, x: 197, y: 602, width: 15.5, height: 133, muscleId: 'tibialis' },
  { id: 'feet-left', svgRaw: femaleFrontAdvancedFeetLeftRaw, x: 343, y: 737, width: 49, height: 56, muscleId: 'feet' },
  { id: 'feet-right', svgRaw: femaleFrontAdvancedFeetRightRaw, x: 162.5, y: 737, width: 49, height: 56, muscleId: 'feet' },
  { id: 'groin', svgRaw: femaleFrontAdvancedGroinRaw, x: 227.5, y: 340.5, width: 97.5, height: 63.5, muscleId: 'groin' },
];

const parsedFemaleFrontAdvancedLayers: ParsedFemaleNormalLayer[] = femaleFrontAdvancedLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

const maleFrontNormalLayers: FemaleNormalLayer[] = [
  { id: 'right_traps', svgRaw: maleFrontTrapsRightRaw, x: 204, y: 132, width: 34, height: 24, muscleId: 'traps' },
  { id: 'Left_traps', svgRaw: maleFrontTrapsLeftRaw, x: 294, y: 132, width: 34, height: 24, muscleId: 'traps' },
  { id: 'right_rear_shoulders_front', svgRaw: maleFrontRearShouldersRightRaw, x: 148.5, y: 155.5, width: 75, height: 58, muscleId: 'rear_delts' },
  { id: 'left_rear_shoulders_front', svgRaw: maleFrontRearShouldersLeftRaw, x: 308.5, y: 155.5, width: 75, height: 58, muscleId: 'rear_delts' },
  { id: 'chest_right', svgRaw: maleFrontChestRightRaw, x: 173.5, y: 157, width: 90, height: 79, muscleId: 'chest' },
  { id: 'chest_left', svgRaw: maleFrontChestLeftRaw, x: 268, y: 157, width: 90, height: 79, muscleId: 'chest' },
  { id: 'right_obliques', svgRaw: maleFrontObliquesRightRaw, x: 185.5, y: 216, width: 44.5, height: 137.5, muscleId: 'obliques' },
  { id: 'left_obliques', svgRaw: maleFrontObliquesLeftRaw, x: 302, y: 216, width: 44.5, height: 137.5, muscleId: 'obliques' },
  { id: 'Abs', svgRaw: maleFrontAbsRaw, x: 230, y: 232, width: 72, height: 166, muscleId: 'abs' },
  { id: 'biceps_right', svgRaw: maleFrontBicepsRightRaw, x: 125.5, y: 211, width: 59.5, height: 76.5, muscleId: 'biceps' },
  { id: 'biceps_left', svgRaw: maleFrontBicepsLeftRaw, x: 347.5, y: 211, width: 59.5, height: 76.5, muscleId: 'biceps' },
  { id: 'right_forearms', svgRaw: maleFrontForearmRightRaw, x: 71, y: 259.5, width: 78.5, height: 107.5, muscleId: 'forearms' },
  { id: 'left_forearms', svgRaw: maleFrontForearmLeftRaw, x: 383, y: 259.5, width: 78.5, height: 107.5, muscleId: 'forearms' },
  { id: 'hands_r_front', svgRaw: maleFrontHandsRightRaw, x: 53, y: 360, width: 33, height: 75.5, muscleId: 'hands' },
  { id: 'hands_l_front', svgRaw: maleFrontHandsLeftRaw, x: 446, y: 360, width: 33, height: 75.5, muscleId: 'hands' },
  { id: 'right_quads', svgRaw: maleFrontQuadRightRaw, x: 185, y: 356.5, width: 78.5, height: 220, muscleId: 'quads', activeMuscles: ['quads', 'adductors'] },
  { id: 'left_quads', svgRaw: maleFrontQuadLeftRaw, x: 268, y: 356.5, width: 78.5, height: 220, muscleId: 'quads', activeMuscles: ['quads', 'adductors'] },
  { id: 'right_calves', svgRaw: maleFrontCalfRightRaw, x: 152.33, y: 591.5, width: 73.17, height: 209, muscleId: 'calves' },
  { id: 'left_calves', svgRaw: maleFrontCalfLeftRaw, x: 307, y: 591.5, width: 73.17, height: 209, muscleId: 'calves' },
];

const parsedMaleFrontNormalLayers: ParsedFemaleNormalLayer[] = maleFrontNormalLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

const maleFrontAdvancedLayers: FemaleNormalLayer[] = [
  { id: 'neck-male-advanced', svgRaw: maleFrontAdvancedNeckRaw, x: 227, y: 108, width: 56.5, height: 53.5, muscleId: 'neck' },
  { id: 'upper-trapezius-left-front', svgRaw: maleFrontAdvancedUpperTrapeziusLeftRaw, x: 285, y: 134, width: 33.5, height: 22.5, muscleId: 'upper_trapezius' },
  { id: 'upper-trapezius-right-front', svgRaw: maleFrontAdvancedUpperTrapeziusRightRaw, x: 193, y: 133.5, width: 33.5, height: 22.5, muscleId: 'upper_trapezius' },
  { id: 'anterior-deltoid-left-front', svgRaw: maleFrontAdvancedAnteriorDeltoidLeftRaw, x: 302, y: 155, width: 54, height: 51, muscleId: 'anterior_deltoid' },
  { id: 'anterior-deltoid-right-front', svgRaw: maleFrontAdvancedAnteriorDeltoidRightRaw, x: 157.5, y: 154.5, width: 54, height: 51, muscleId: 'anterior_deltoid' },
  { id: 'lateral-deltoid-left-front', svgRaw: maleFrontAdvancedLateralDeltoidLeftRaw, x: 332, y: 156, width: 44.5, height: 55.5, muscleId: 'lateral_deltoid' },
  { id: 'lateral-deltoid-right-front', svgRaw: maleFrontAdvancedLateralDeltoidRightRaw, x: 135.5, y: 156.5, width: 44.5, height: 55.5, muscleId: 'lateral_deltoid' },
  { id: 'upper-pectoralis-left-front', svgRaw: maleFrontAdvancedUpperPectoralisLeftRaw, x: 271, y: 158, width: 76.5, height: 48.5, muscleId: 'upper_pectoralis' },
  { id: 'upper-pectoralis-right-front', svgRaw: maleFrontAdvancedUpperPectoralisRightRaw, x: 164.5, y: 157.5, width: 76.5, height: 48.5, muscleId: 'upper_pectoralis' },
  { id: 'mid-lower-pectoralis-left-front', svgRaw: maleFrontAdvancedMidLowerPectoralisLeftRaw, x: 257, y: 160, width: 88, height: 75.5, muscleId: 'mid_lower_pectoralis' },
  { id: 'mid-lower-pectoralis-right-front', svgRaw: maleFrontAdvancedMidLowerPectoralisRightRaw, x: 165, y: 160, width: 88.5, height: 75.5, muscleId: 'mid_lower_pectoralis' },
  { id: 'long-head-bicep-left-front', svgRaw: maleFrontAdvancedLongHeadBicepLeftRaw, x: 358.5, y: 211, width: 43, height: 70, muscleId: 'long_head_bicep' },
  { id: 'long-head-bicep-right-front', svgRaw: maleFrontAdvancedLongHeadBicepRightRaw, x: 109, y: 211, width: 43, height: 70, muscleId: 'long_head_bicep' },
  { id: 'short-head-bicep-left-front', svgRaw: maleFrontAdvancedShortHeadBicepLeftRaw, x: 339, y: 212.5, width: 51.5, height: 71.5, muscleId: 'short_head_bicep' },
  { id: 'short-head-bicep-right-front', svgRaw: maleFrontAdvancedShortHeadBicepRightRaw, x: 120, y: 213, width: 51.5, height: 71.5, muscleId: 'short_head_bicep' },
  { id: 'wrist-extensors-left-front', svgRaw: maleFrontAdvancedWristExtensorsLeftRaw, x: 399, y: 265, width: 58, height: 99.5, muscleId: 'wrist_extensors' },
  { id: 'wrist-extensors-right-front', svgRaw: maleFrontAdvancedWristExtensorsRightRaw, x: 54, y: 267, width: 58, height: 99.5, muscleId: 'wrist_extensors' },
  { id: 'wrist-flexors-left-front', svgRaw: maleFrontAdvancedWristFlexorsLeftRaw, x: 377, y: 287, width: 71.5, height: 80.5, muscleId: 'wrist_flexors' },
  { id: 'wrist-flexors-right-front', svgRaw: maleFrontAdvancedWristFlexorsRightRaw, x: 63.5, y: 286, width: 71.5, height: 80.5, muscleId: 'wrist_flexors' },
  { id: 'hands-left-front', svgRaw: maleFrontAdvancedHandsLeftRaw, x: 441, y: 363, width: 34, height: 72.5, muscleId: 'hands' },
  { id: 'hands-right-front', svgRaw: maleFrontAdvancedHandsRightRaw, x: 36.5, y: 363, width: 34, height: 72.5, muscleId: 'hands' },
  { id: 'abs-up-male-advanced', svgRaw: maleFrontAdvancedAbsUpRaw, x: 218, y: 231.5, width: 74, height: 60.5, muscleId: 'abs_up' },
  { id: 'abs-down-male-advanced', svgRaw: maleFrontAdvancedAbsDownRaw, x: 223, y: 295.5, width: 64, height: 102.5, muscleId: 'abs_down' },
  { id: 'obliques-left-male-advanced', svgRaw: maleFrontAdvancedObliquesLeftRaw, x: 175, y: 219, width: 43.5, height: 133, muscleId: 'obliques' },
  { id: 'obliques-right-male-advanced', svgRaw: maleFrontAdvancedObliquesRightRaw, x: 292, y: 218.5, width: 43.5, height: 133.5, muscleId: 'obliques' },
  { id: 'rectus-femoris-left-front', svgRaw: maleFrontAdvancedRectusFemorisLeftRaw, x: 288.5, y: 368.5, width: 30.5, height: 209.5, muscleId: 'rectus_femoris' },
  { id: 'rectus-femoris-right-front', svgRaw: maleFrontAdvancedRectusFemorisRightRaw, x: 192, y: 371, width: 30.5, height: 209.5, muscleId: 'rectus_femoris' },
  { id: 'outer-quadricep-left-front', svgRaw: maleFrontAdvancedOuterQuadricepLeftRaw, x: 311.5, y: 359.5, width: 29.5, height: 199.5, muscleId: 'outer_quadricep' },
  { id: 'outer-quadricep-right-front', svgRaw: maleFrontAdvancedOuterQuadricepRightRaw, x: 170, y: 360, width: 29.5, height: 199.5, muscleId: 'outer_quadricep' },
  { id: 'inner-quadricep-left-front', svgRaw: maleFrontAdvancedInnerQuadricepLeftRaw, x: 277, y: 486.27, width: 13.5, height: 75.5, muscleId: 'inner_quadricep' },
  { id: 'inner-quadricep-right-front', svgRaw: maleFrontAdvancedInnerQuadricepRightRaw, x: 220, y: 486.27, width: 13.5, height: 75.5, muscleId: 'inner_quadricep' },
  { id: 'inner-thigh-left-front', svgRaw: maleFrontAdvancedInnerThighLeftRaw, x: 257, y: 357, width: 63, height: 151, muscleId: 'inner_thigh' },
  { id: 'inner-thigh-right-front', svgRaw: maleFrontAdvancedInnerThighRightRaw, x: 190.5, y: 356.5, width: 63, height: 151, muscleId: 'inner_thigh' },
  { id: 'gastrocnemius-left-front', svgRaw: maleFrontAdvancedGastrocnemiusLeftRaw, x: 296, y: 603, width: 27, height: 129, muscleId: 'gastrocnemius' },
  { id: 'gastrocnemius-right-front', svgRaw: maleFrontAdvancedGastrocnemiusRightRaw, x: 188, y: 603.5, width: 27, height: 129, muscleId: 'gastrocnemius' },
  { id: 'soleus-left-front', svgRaw: maleFrontAdvancedSoleusLeftRaw, x: 330, y: 593, width: 16.5, height: 140.5, muscleId: 'soleus' },
  { id: 'soleus-right-front', svgRaw: maleFrontAdvancedSoleusRightRaw, x: 165.5, y: 592.5, width: 16.5, height: 140.5, muscleId: 'soleus' },
  { id: 'tibialis-left-front', svgRaw: maleFrontAdvancedTibialisLeftRaw, x: 313, y: 603, width: 20, height: 131, muscleId: 'tibialis' },
  { id: 'tibialis-right-front', svgRaw: maleFrontAdvancedTibialisRightRaw, x: 179.5, y: 602.5, width: 20, height: 131, muscleId: 'tibialis' },
  { id: 'feet-left-front', svgRaw: maleFrontAdvancedFeetLeftRaw, x: 316, y: 734, width: 56.5, height: 68, muscleId: 'feet' },
  { id: 'feet-right-front', svgRaw: maleFrontAdvancedFeetRightRaw, x: 140, y: 733.5, width: 56.5, height: 68, muscleId: 'feet' },
  { id: 'groin-male-advanced', svgRaw: maleFrontAdvancedGroinRaw, x: 205, y: 359, width: 100, height: 76.5, muscleId: 'groin' },
];

const parsedMaleFrontAdvancedLayers: ParsedFemaleNormalLayer[] = maleFrontAdvancedLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

const maleBackNormalLayers: FemaleNormalLayer[] = [
  { id: 'traps', svgRaw: maleBackTrapsTopRaw, x: 247, y: 139.5, width: 118, height: 27, muscleId: 'traps' },
  { id: 'traps-middle', svgRaw: maleBackTrapsMiddleRaw, x: 269, y: 167, width: 72, height: 84.5, muscleId: 'traps_middle' },
  { id: 'left-rear-shoulders', svgRaw: maleBackRearShoulderLeftRaw, x: 189, y: 153.5, width: 68, height: 44, muscleId: 'rear_delts' },
  { id: 'right-rear-shoulders', svgRaw: maleBackRearShoulderRightRaw, x: 352.5, y: 153.5, width: 68, height: 44, muscleId: 'rear_delts' },
  { id: 'left-lats', svgRaw: maleBackLatsLeftRaw, x: 218.5, y: 166.5, width: 74.5, height: 189, muscleId: 'lats' },
  { id: 'right-lats', svgRaw: maleBackLatsRightRaw, x: 316, y: 167, width: 74.5, height: 189, muscleId: 'lats' },
  { id: 'lowerback', svgRaw: maleBackLowerBackRaw, x: 273, y: 248, width: 62.5, height: 110.5, muscleId: 'lower_back' },
  { id: 'left-triceps', svgRaw: maleBackTricepsLeftRaw, x: 156, y: 203, width: 61, height: 76, muscleId: 'triceps' },
  { id: 'right-triceps', svgRaw: maleBackTricepsRightRaw, x: 393, y: 202.5, width: 61, height: 76, muscleId: 'triceps' },
  { id: 'left-forearms', svgRaw: maleBackForearmsLeftRaw, x: 102, y: 267, width: 77.5, height: 104.5, muscleId: 'forearms' },
  { id: 'right-forearms', svgRaw: maleBackForearmsRightRaw, x: 429, y: 267, width: 77.5, height: 104.5, muscleId: 'forearms' },
  { id: 'hands_r_back_normal_male', svgRaw: maleBackHandsRightRaw, x: 92, y: 366, width: 30.5, height: 72, muscleId: 'hands' },
  { id: 'hands_l_back_normal_male', svgRaw: maleBackHandsLeftRaw, x: 487, y: 366, width: 30.5, height: 72, muscleId: 'hands' },
  { id: 'left-glutes', svgRaw: maleBackGlutesLeftRaw, x: 244, y: 346, width: 59.5, height: 85.5, muscleId: 'glutes' },
  { id: 'right-glutes', svgRaw: maleBackGlutesRightRaw, x: 308.5, y: 346.5, width: 59.5, height: 85.5, muscleId: 'glutes' },
  { id: 'left-hamstring', svgRaw: maleBackHamstringsLeftRaw, x: 219, y: 356, width: 81.5, height: 219.5, muscleId: 'hamstrings' },
  { id: 'right-hamstring', svgRaw: maleBackHamstringsRightRaw, x: 308.5, y: 355.5, width: 81.5, height: 219.5, muscleId: 'hamstrings' },
  { id: 'left-calve', svgRaw: maleBackCalvesLeftRaw, x: 213, y: 607, width: 52.5, height: 72.5, muscleId: 'calves' },
  { id: 'right-calve', svgRaw: maleBackCalvesRightRaw, x: 345, y: 606.5, width: 52.5, height: 72.5, muscleId: 'calves' },
];

const parsedMaleBackNormalLayers: ParsedFemaleNormalLayer[] = maleBackNormalLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

const femaleBackNormalLayers: FemaleNormalLayer[] = [
  { id: 'traps', svgRaw: femaleBackTrapsTopRaw, x: 251, y: 126, width: 112, height: 26.5, muscleId: 'traps' },
  { id: 'left-rear-shoulders', svgRaw: femaleBackRearShoulderLeftRaw, x: 208, y: 146, width: 58, height: 44, muscleId: 'rear_delts' },
  { id: 'right-rear-shoulders', svgRaw: femaleBackRearShoulderRightRaw, x: 348, y: 146, width: 58, height: 44, muscleId: 'rear_delts' },
  { id: 'traps-middle', svgRaw: femaleBackTrapsMiddleRaw, x: 269, y: 151, width: 76, height: 83.61, muscleId: 'traps_middle' },
  { id: 'left-lats', svgRaw: femaleBackLatsLeftRaw, x: 237.5, y: 158, width: 60.5, height: 160, muscleId: 'lats' },
  { id: 'right-lats', svgRaw: femaleBackLatsRightRaw, x: 316, y: 158, width: 60.5, height: 160, muscleId: 'lats' },
  { id: 'lowerback', svgRaw: femaleBackLowerBackRaw, x: 275, y: 237, width: 63.5, height: 107.5, muscleId: 'lower_back' },
  { id: 'left-triceps', svgRaw: femaleBackTricepsLeftRaw, x: 174, y: 185, width: 62.15, height: 81, muscleId: 'triceps' },
  { id: 'right-triceps', svgRaw: femaleBackTricepsRightRaw, x: 377.98, y: 185, width: 62.15, height: 81, muscleId: 'triceps' },
  { id: 'left-forearms', svgRaw: femaleBackForearmsLeftRaw, x: 118.43, y: 247.14, width: 71.4, height: 94.65, muscleId: 'forearms' },
  { id: 'right-forearms', svgRaw: femaleBackForearmsRightRaw, x: 424, y: 247.14, width: 71.4, height: 94.65, muscleId: 'forearms' },
  { id: 'hands_l_back_normal', svgRaw: femaleBackHandsLeftRaw, x: 93, y: 334, width: 34.5, height: 78, muscleId: 'hands' },
  { id: 'hands_r_back_normal', svgRaw: femaleBackHandsRightRaw, x: 486, y: 334, width: 34.5, height: 78, muscleId: 'hands' },
  { id: 'left-glutes', svgRaw: femaleBackGlutesLeftRaw, x: 240.9, y: 319.25, width: 63.28, height: 96.73, muscleId: 'glutes' },
  { id: 'right-glutes', svgRaw: femaleBackGlutesRightRaw, x: 310, y: 319.25, width: 63.28, height: 96.73, muscleId: 'glutes' },
  { id: 'left-hamstring', svgRaw: femaleBackHamstringsLeftRaw, x: 224.5, y: 318.08, width: 74.05, height: 251.42, muscleId: 'hamstrings' },
  { id: 'right-hamstring', svgRaw: femaleBackHamstringsRightRaw, x: 316, y: 318.08, width: 74.05, height: 251.42, muscleId: 'hamstrings' },
  { id: 'left-calve', svgRaw: femaleBackCalvesLeftRaw, x: 214, y: 580.42, width: 44, height: 98.22, muscleId: 'calves' },
  { id: 'right-calve', svgRaw: femaleBackCalvesRightRaw, x: 356, y: 580.42, width: 44, height: 98.22, muscleId: 'calves' },
];

const parsedFemaleBackNormalLayers: ParsedFemaleNormalLayer[] = femaleBackNormalLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

const femaleBackAdvancedLayers: FemaleNormalLayer[] = [
  { id: 'neck-back', svgRaw: femaleBackAdvancedNeckRaw, x: 285, y: 99.5, width: 47.5, height: 24.5, muscleId: 'neck' },
  { id: 'upper-trapezius', svgRaw: femaleBackAdvancedUpperTrapeziusRaw, x: 248, y: 123, width: 119, height: 27, muscleId: 'upper_trapezius' },
  { id: 'traps-middle-advanced', svgRaw: femaleBackAdvancedTrapsMiddleRaw, x: 268.5, y: 148, width: 79.5, height: 53.5, muscleId: 'traps_middle' },
  { id: 'lower-trapezius', svgRaw: femaleBackAdvancedLowerTrapeziusRaw, x: 292.5, y: 203.5, width: 31, height: 30, muscleId: 'lower_trapezius' },
  { id: 'lateral-deltoid-left-back', svgRaw: femaleBackAdvancedLateralDeltoidLeftRaw, x: 206, y: 143.5, width: 43.5, height: 43, muscleId: 'lateral_deltoid' },
  { id: 'lateral-deltoid-right-back', svgRaw: femaleBackAdvancedLateralDeltoidRightRaw, x: 367, y: 143.5, width: 43.5, height: 43, muscleId: 'lateral_deltoid' },
  { id: 'posterior-deltoid-left', svgRaw: femaleBackAdvancedPosteriorDeltoidLeftRaw, x: 220.5, y: 145.5, width: 46, height: 38, muscleId: 'posterior_deltoid' },
  { id: 'posterior-deltoid-right', svgRaw: femaleBackAdvancedPosteriorDeltoidRightRaw, x: 350, y: 145.5, width: 46, height: 38, muscleId: 'posterior_deltoid' },
  { id: 'long-head-triceps-left', svgRaw: femaleBackAdvancedLongHeadTricepsLeftRaw, x: 199, y: 182.5, width: 37, height: 68, muscleId: 'long_head_triceps' },
  { id: 'long-head-triceps-right', svgRaw: femaleBackAdvancedLongHeadTricepsRightRaw, x: 380, y: 182.5, width: 37, height: 68, muscleId: 'long_head_triceps' },
  { id: 'lateral-head-triceps-left', svgRaw: femaleBackAdvancedLateralHeadTricepsLeftRaw, x: 177.5, y: 184, width: 53.5, height: 47, muscleId: 'lateral_head_triceps' },
  { id: 'lateral-head-triceps-right', svgRaw: femaleBackAdvancedLateralHeadTricepsRightRaw, x: 385, y: 184, width: 53.5, height: 47, muscleId: 'lateral_head_triceps' },
  { id: 'medial-head-triceps-left', svgRaw: femaleBackAdvancedMedialHeadTricepsLeftRaw, x: 170.5, y: 208.5, width: 43, height: 56, muscleId: 'medial_head_triceps' },
  { id: 'medial-head-triceps-right', svgRaw: femaleBackAdvancedMedialHeadTricepsRightRaw, x: 402.5, y: 208.5, width: 43, height: 56, muscleId: 'medial_head_triceps' },
  { id: 'wrist-extensors-left-back', svgRaw: femaleBackAdvancedWristExtensorsLeftRaw, x: 114.5, y: 246, width: 62.5, height: 90, muscleId: 'wrist_extensors' },
  { id: 'wrist-extensors-right-back', svgRaw: femaleBackAdvancedWristExtensorsRightRaw, x: 439, y: 246, width: 62.5, height: 90, muscleId: 'wrist_extensors' },
  { id: 'wrist-flexors-left-back', svgRaw: femaleBackAdvancedWristFlexorsLeftRaw, x: 116.5, y: 253, width: 71.5, height: 88, muscleId: 'wrist_flexors' },
  { id: 'wrist-flexors-right-back', svgRaw: femaleBackAdvancedWristFlexorsRightRaw, x: 428, y: 253, width: 71.5, height: 88, muscleId: 'wrist_flexors' },
  { id: 'hands-left-back', svgRaw: femaleBackAdvancedHandsLeftRaw, x: 89, y: 331.5, width: 34.5, height: 78, muscleId: 'hands' },
  { id: 'hands-right-back', svgRaw: femaleBackAdvancedHandsRightRaw, x: 492.5, y: 331.5, width: 34.5, height: 78, muscleId: 'hands' },
  { id: 'lats-left-advanced', svgRaw: femaleBackAdvancedLatsLeftRaw, x: 236.5, y: 155, width: 62, height: 161.5, muscleId: 'lats' },
  { id: 'lats-right-advanced', svgRaw: femaleBackAdvancedLatsRightRaw, x: 317.5, y: 155, width: 62, height: 161.5, muscleId: 'lats' },
  { id: 'lower-back-advanced', svgRaw: femaleBackAdvancedLowerBackRaw, x: 275, y: 233.5, width: 66.5, height: 110, muscleId: 'lower_back' },
  { id: 'gluteus-medius-left', svgRaw: femaleBackAdvancedGluteusMediusLeftRaw, x: 242.5, y: 316.5, width: 38.5, height: 45.5, muscleId: 'gluteus_medius' },
  { id: 'gluteus-medius-right', svgRaw: femaleBackAdvancedGluteusMediusRightRaw, x: 335, y: 316.5, width: 38.5, height: 46, muscleId: 'gluteus_medius' },
  { id: 'gluteus-maximus-left', svgRaw: femaleBackAdvancedGluteusMaximusLeftRaw, x: 240.5, y: 318, width: 65, height: 97, muscleId: 'gluteus_maximus' },
  { id: 'gluteus-maximus-right', svgRaw: femaleBackAdvancedGluteusMaximusRightRaw, x: 310.5, y: 318, width: 65, height: 97, muscleId: 'gluteus_maximus' },
  { id: 'inner-thigh-left-back', svgRaw: femaleBackAdvancedInnerThighLeftRaw, x: 278.5, y: 408, width: 21.5, height: 57, muscleId: 'inner_thigh' },
  { id: 'inner-thigh-right-back', svgRaw: femaleBackAdvancedInnerThighRightRaw, x: 316.5, y: 408, width: 21.5, height: 57, muscleId: 'inner_thigh' },
  { id: 'medial-hamstrings-left', svgRaw: femaleBackAdvancedMedialHamstringsLeftRaw, x: 254, y: 416, width: 31, height: 152.5, muscleId: 'medial_hamstrings' },
  { id: 'medial-hamstrings-right', svgRaw: femaleBackAdvancedMedialHamstringsRightRaw, x: 331.5, y: 416, width: 31, height: 152.5, muscleId: 'medial_hamstrings' },
  { id: 'lateral-hamstrings-left', svgRaw: femaleBackAdvancedLateralHamstringsLeftRaw, x: 223.5, y: 316.5, width: 37, height: 239, muscleId: 'lateral_hamstrings' },
  { id: 'lateral-hamstrings-right', svgRaw: femaleBackAdvancedLateralHamstringsRightRaw, x: 355.75, y: 316.5, width: 37, height: 239, muscleId: 'lateral_hamstrings' },
  { id: 'soleus-left-back', svgRaw: femaleBackAdvancedSoleusLeftRaw, x: 211.5, y: 579.5, width: 23.5, height: 94, muscleId: 'soleus' },
  { id: 'soleus-right-back', svgRaw: femaleBackAdvancedSoleusRightRaw, x: 381, y: 579.5, width: 23.5, height: 94, muscleId: 'soleus' },
  { id: 'gastrocnemius-left-back', svgRaw: femaleBackAdvancedGastrocnemiusLeftRaw, x: 237.5, y: 599.5, width: 21, height: 77.5, muscleId: 'gastrocnemius' },
  { id: 'gastrocnemius-right-back', svgRaw: femaleBackAdvancedGastrocnemiusRightRaw, x: 357.5, y: 599.5, width: 21, height: 77.5, muscleId: 'gastrocnemius' },
  { id: 'feet-left-back', svgRaw: femaleBackAdvancedFeetLeftRaw, x: 198.5, y: 737.5, width: 42.5, height: 62.5, muscleId: 'feet' },
  { id: 'feet-right-back', svgRaw: femaleBackAdvancedFeetRightRaw, x: 375, y: 737.5, width: 42.5, height: 62.5, muscleId: 'feet' },
];

const parsedFemaleBackAdvancedLayers: ParsedFemaleNormalLayer[] = femaleBackAdvancedLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

const maleBackAdvancedLayers: FemaleNormalLayer[] = [
  { id: 'neck-back-male-advanced', svgRaw: maleBackAdvancedNeckRaw, x: 270.5, y: 106, width: 62, height: 33, muscleId: 'neck' },
  { id: 'upper-trapezius-back-male-advanced', svgRaw: maleBackAdvancedUpperTrapeziusRaw, x: 237, y: 141.5, width: 127.5, height: 28, muscleId: 'upper_trapezius' },
  { id: 'traps-middle-back-male-advanced', svgRaw: maleBackAdvancedTrapsMiddleRaw, x: 262.5, y: 169.5, width: 79, height: 45, muscleId: 'traps_middle' },
  { id: 'lower-trapezius-back-male-advanced', svgRaw: maleBackAdvancedLowerTrapeziusRaw, x: 283, y: 217.5, width: 37, height: 40, muscleId: 'lower_trapezius' },
  { id: 'lateral-deltoid-left-back-male-advanced', svgRaw: maleBackAdvancedLateralDeltoidLeftRaw, x: 180, y: 156.5, width: 58, height: 48, muscleId: 'lateral_deltoid' },
  { id: 'lateral-deltoid-right-back-male-advanced', svgRaw: maleBackAdvancedLateralDeltoidRightRaw, x: 365, y: 156, width: 58, height: 48, muscleId: 'lateral_deltoid' },
  { id: 'posterior-deltoid-left-back-male-advanced', svgRaw: maleBackAdvancedPosteriorDeltoidLeftRaw, x: 201, y: 158, width: 53.5, height: 42.5, muscleId: 'posterior_deltoid' },
  { id: 'posterior-deltoid-right-back-male-advanced', svgRaw: maleBackAdvancedPosteriorDeltoidRightRaw, x: 349.5, y: 158, width: 53.5, height: 42.5, muscleId: 'posterior_deltoid' },
  { id: 'long-head-triceps-left-back-male-advanced', svgRaw: maleBackAdvancedLongHeadTricepsLeftRaw, x: 185, y: 204.5, width: 28.5, height: 68, muscleId: 'long_head_triceps' },
  { id: 'long-head-triceps-right-back-male-advanced', svgRaw: maleBackAdvancedLongHeadTricepsRightRaw, x: 389, y: 204, width: 28.5, height: 68, muscleId: 'long_head_triceps' },
  { id: 'lateral-head-triceps-left-back-male-advanced', svgRaw: maleBackAdvancedLateralHeadTricepsLeftRaw, x: 152, y: 202, width: 55.5, height: 53.5, muscleId: 'lateral_head_triceps' },
  { id: 'lateral-head-triceps-right-back-male-advanced', svgRaw: maleBackAdvancedLateralHeadTricepsRightRaw, x: 397, y: 203, width: 55.5, height: 53.5, muscleId: 'lateral_head_triceps' },
  { id: 'medial-head-triceps-left-back-male-advanced', svgRaw: maleBackAdvancedMedialHeadTricepsLeftRaw, x: 148, y: 226, width: 43.5, height: 60, muscleId: 'medial_head_triceps' },
  { id: 'medial-head-triceps-right-back-male-advanced', svgRaw: maleBackAdvancedMedialHeadTricepsRightRaw, x: 412.5, y: 226, width: 43.5, height: 60, muscleId: 'medial_head_triceps' },
  { id: 'wrist-extensors-left-back-male-advanced', svgRaw: maleBackAdvancedWristExtensorsLeftRaw, x: 93, y: 269, width: 67.5, height: 106, muscleId: 'wrist_extensors' },
  { id: 'wrist-extensors-right-back-male-advanced', svgRaw: maleBackAdvancedWristExtensorsRightRaw, x: 443.5, y: 269, width: 67.5, height: 106, muscleId: 'wrist_extensors' },
  { id: 'wrist-flexors-left-back-male-advanced', svgRaw: maleBackAdvancedWristFlexorsLeftRaw, x: 99, y: 273.5, width: 77, height: 104, muscleId: 'wrist_flexors' },
  { id: 'wrist-flexors-right-back-male-advanced', svgRaw: maleBackAdvancedWristFlexorsRightRaw, x: 429, y: 274, width: 77, height: 104, muscleId: 'wrist_flexors' },
  { id: 'hands-left-back-male-advanced', svgRaw: maleBackAdvancedHandsLeftRaw, x: 82, y: 374, width: 32, height: 71, muscleId: 'hands' },
  { id: 'hands-right-back-male-advanced', svgRaw: maleBackAdvancedHandsRightRaw, x: 487, y: 374, width: 32, height: 71, muscleId: 'hands' },
  { id: 'lats-left-back-male-advanced', svgRaw: maleBackAdvancedLatsLeftRaw, x: 214, y: 169, width: 76, height: 199.5, muscleId: 'lats' },
  { id: 'lats-right-back-male-advanced', svgRaw: maleBackAdvancedLatsRightRaw, x: 314.5, y: 168.5, width: 76, height: 199.5, muscleId: 'lats' },
  { id: 'lower-back-male-advanced', svgRaw: maleBackAdvancedLowerBackRaw, x: 266, y: 249.5, width: 70.5, height: 115, muscleId: 'lower_back' },
  { id: 'gluteus-medius-left-back-male-advanced', svgRaw: maleBackAdvancedGluteusMediusLeftRaw, x: 237, y: 352, width: 34, height: 45.5, muscleId: 'gluteus_medius' },
  { id: 'gluteus-medius-right-back-male-advanced', svgRaw: maleBackAdvancedGluteusMediusRightRaw, x: 330.5, y: 351.5, width: 34, height: 45.5, muscleId: 'gluteus_medius' },
  { id: 'gluteus-maximus-left-back-male-advanced', svgRaw: maleBackAdvancedGluteusMaximusLeftRaw, x: 236, y: 350, width: 63.5, height: 87.5, muscleId: 'gluteus_maximus' },
  { id: 'gluteus-maximus-right-back-male-advanced', svgRaw: maleBackAdvancedGluteusMaximusRightRaw, x: 303, y: 350.5, width: 63.5, height: 87.5, muscleId: 'gluteus_maximus' },
  { id: 'inner-thigh-left-back-male-advanced', svgRaw: maleBackAdvancedInnerThighLeftRaw, x: 283.5, y: 436, width: 15.5, height: 39.5, muscleId: 'inner_thigh' },
  { id: 'inner-thigh-right-back-male-advanced', svgRaw: maleBackAdvancedInnerThighRightRaw, x: 305, y: 436, width: 15.5, height: 39.5, muscleId: 'inner_thigh' },
  { id: 'medial-hamstrings-left-back-male-advanced', svgRaw: maleBackAdvancedMedialHamstringsLeftRaw, x: 250, y: 441, width: 39, height: 142.5, muscleId: 'medial_hamstrings' },
  { id: 'medial-hamstrings-right-back-male-advanced', svgRaw: maleBackAdvancedMedialHamstringsRightRaw, x: 313.5, y: 440.5, width: 39, height: 142.5, muscleId: 'medial_hamstrings' },
  { id: 'lateral-hamstrings-left-back-male-advanced', svgRaw: maleBackAdvancedLateralHamstringsLeftRaw, x: 214, y: 361, width: 40, height: 212, muscleId: 'lateral_hamstrings' },
  { id: 'lateral-hamstrings-right-back-male-advanced', svgRaw: maleBackAdvancedLateralHamstringsRightRaw, x: 348.5, y: 360.5, width: 40, height: 212, muscleId: 'lateral_hamstrings' },
  { id: 'soleus-left-back-male-advanced', svgRaw: maleBackAdvancedSoleusLeftRaw, x: 204, y: 610, width: 27, height: 76, muscleId: 'soleus' },
  { id: 'soleus-right-back-male-advanced', svgRaw: maleBackAdvancedSoleusRightRaw, x: 370, y: 609.5, width: 27, height: 76, muscleId: 'soleus' },
  { id: 'gastrocnemius-left-back-male-advanced', svgRaw: maleBackAdvancedGastrocnemiusLeftRaw, x: 236, y: 618, width: 23.5, height: 69, muscleId: 'gastrocnemius' },
  { id: 'gastrocnemius-right-back-male-advanced', svgRaw: maleBackAdvancedGastrocnemiusRightRaw, x: 342.5, y: 618.5, width: 23.5, height: 69, muscleId: 'gastrocnemius' },
  { id: 'feet-left-back-male-advanced', svgRaw: maleBackAdvancedFeetLeftRaw, x: 180, y: 738, width: 56, height: 66.5, muscleId: 'feet' },
  { id: 'feet-right-back-male-advanced', svgRaw: maleBackAdvancedFeetRightRaw, x: 364.5, y: 738, width: 56, height: 66.5, muscleId: 'feet' },
];

const parsedMaleBackAdvancedLayers: ParsedFemaleNormalLayer[] = maleBackAdvancedLayers.map((layer) => ({
  ...layer,
  ...parseSvgLayer(layer.svgRaw),
}));

// Normal muscle mapping (muscle groups)
const normalFrontMuscles = [
  'neck', 'front_delts', 'chest', 'biceps', 'forearms', 'abs', 'obliques', 'quads', 'adductors', 'tibialis'
];
const normalBackMuscles = [
  'traps', 'rear_delts', 'triceps', 'forearms', 'lats', 'lower_back', 'glutes', 'hamstrings', 'calves'
];

// Advanced muscle mapping (detailed)
const advancedFrontMuscles = [
  'neck',
  'upper_chest', 'middle_chest', 'lower_chest', 'inner_chest',
  'front_delts', 'side_delts',
  'biceps_long_left', 'biceps_short_left', 'biceps_long_right', 'biceps_short_right',
  'forearms',
  'upper_abs', 'middle_abs', 'lower_abs', 'serratus', 'obliques',
  'rectus_femoris', 'vastus_lateralis', 'vastus_medialis',
  'tibialis', 'gastrocnemius', 'soleus',
];
const advancedBackMuscles = [
  'neck',
  'upper_trapezius', 'traps_middle', 'lower_trapezius',
  'posterior_deltoid',
  'long_head_triceps', 'lateral_head_triceps', 'medial_head_triceps',
  'lats',
  'lower_back',
  'gluteus_maximus', 'gluteus_medius',
  'lateral_hamstrings', 'medial_hamstrings',
  'gastrocnemius', 'soleus',
];

// Map advanced muscles to their parent group for exercise filtering
const advancedToGroupMap: Record<string, string> = {
  // File-based detailed IDs
  upper_pectoralis: 'chest',
  mid_lower_pectoralis: 'chest',
  anterior_deltoid: 'shoulders',
  lateral_deltoid: 'shoulders',
  posterior_deltoid: 'shoulders',
  upper_trapezius: 'back',
  traps_middle: 'back',
  lower_trapezius: 'back',
  long_head_bicep: 'biceps',
  short_head_bicep: 'biceps',
  long_head_bicep_left: 'biceps',
  short_head_bicep_left: 'biceps',
  long_head_bicep_right: 'biceps',
  short_head_bicep_right: 'biceps',
  wrist_extensors: 'biceps',
  wrist_flexors: 'biceps',
  hands: 'biceps',
  abs_up: 'abs',
  abs_down: 'abs',
  outer_quadricep: 'quads',
  inner_quadricep: 'quads',
  inner_thigh: 'quads',
  feet: 'calves',
  groin: 'quads',
  long_head_triceps: 'triceps',
  lateral_head_triceps: 'triceps',
  medial_head_triceps: 'triceps',
  long_head_triceps_left: 'triceps',
  lateral_head_triceps_left: 'triceps',
  medial_head_triceps_left: 'triceps',
  long_head_triceps_right: 'triceps',
  lateral_head_triceps_right: 'triceps',
  medial_head_triceps_right: 'triceps',
  medial_hamstrings: 'hamstrings',
  lateral_hamstrings: 'hamstrings',

  // Legacy advanced IDs
  upper_chest: 'chest', middle_chest: 'chest', lower_chest: 'chest', inner_chest: 'chest',
  front_delts: 'shoulders', side_delts: 'shoulders', rear_delts: 'shoulders',
  biceps_long_left: 'biceps', biceps_short_left: 'biceps', biceps_long_right: 'biceps', biceps_short_right: 'biceps',
  upper_abs: 'abs', middle_abs: 'abs', lower_abs: 'abs', serratus: 'abs', obliques: 'abs',
  rectus_femoris: 'quads', vastus_lateralis: 'quads', vastus_medialis: 'quads',
  upper_traps: 'back', middle_traps: 'back', lower_traps: 'back',
  upper_lats: 'back', middle_lats: 'back', lower_lats: 'back',
  teres_major: 'back', teres_minor: 'back', erector_spinae: 'back',
  triceps_long_left: 'triceps', triceps_lateral_left: 'triceps', triceps_medial_left: 'triceps',
  triceps_long_right: 'triceps', triceps_lateral_right: 'triceps', triceps_medial_right: 'triceps',
  gluteus_maximus: 'glutes', gluteus_medius: 'glutes',
  biceps_femoris: 'hamstrings', semitendinosus: 'hamstrings', semimembranosus: 'hamstrings',
  gastrocnemius: 'calves', soleus: 'calves',
  chest: 'chest', traps: 'back', lats: 'back', lower_back: 'back',
  biceps: 'biceps', triceps: 'triceps', abs: 'abs',
  quads: 'quads', hamstrings: 'hamstrings', glutes: 'glutes', calves: 'calves',
  adductors: 'quads', tibialis: 'calves', neck: 'shoulders', forearms: 'biceps',
};

// Label names for advanced muscles
const muscleLabels: Record<string, MuscleLabel> = {
  // Normal
  chest: { en: 'Chest', ar: 'الصدر' },
  neck: { en: 'Neck', ar: 'الرقبة' },
  front_delts: { en: 'Front Delts', ar: 'الكتف الأمامي' },
  biceps: { en: 'Biceps', ar: 'الباي' },
  forearms: { en: 'Forearms', ar: 'الساعد' },
  abs: { en: 'Abs', ar: 'البطن' },
  obliques: { en: 'Obliques', ar: 'المائلة' },
  quads: { en: 'Quads', ar: 'الفخذ الأمامي' },
  adductors: { en: 'Adductors', ar: 'المقرّبة' },
  tibialis: { en: 'Tibialis', ar: 'الساق الأمامي' },
  traps: { en: 'Traps', ar: 'الترابس' },
  rear_delts: { en: 'Rear Delts', ar: 'الكتف الخلفي' },
  triceps: { en: 'Triceps', ar: 'التراي' },
  lats: { en: 'Lats', ar: 'المجنص' },
  lower_back: { en: 'Lower Back', ar: 'أسفل الظهر' },
  glutes: { en: 'Glutes', ar: 'المؤخرة' },
  hamstrings: { en: 'Hamstrings', ar: 'الفخذ الخلفي' },
  calves: { en: 'Calves', ar: 'السمانة' },
  // Advanced
  upper_pectoralis: { en: 'Upper Pectoralis', ar: 'Upper Pectoralis' },
  mid_lower_pectoralis: { en: 'Mid-Lower Pectoralis', ar: 'Mid-Lower Pectoralis' },
  anterior_deltoid: { en: 'Anterior Deltoid', ar: 'Anterior Deltoid' },
  lateral_deltoid: { en: 'Lateral Deltoid', ar: 'Lateral Deltoid' },
  posterior_deltoid: { en: 'Posterior Deltoid', ar: 'Posterior Deltoid' },
  upper_trapezius: { en: 'Upper Trapezius', ar: 'Upper Trapezius' },
  traps_middle: { en: 'Traps Middle', ar: 'Traps Middle' },
  lower_trapezius: { en: 'Lower Trapezius', ar: 'Lower Trapezius' },
  long_head_bicep: { en: 'Long Head Bicep', ar: 'Long Head Bicep' },
  short_head_bicep: { en: 'Short Head Bicep', ar: 'Short Head Bicep' },
  long_head_bicep_left: { en: 'Long Head Bicep (L)', ar: 'Long Head Bicep (L)' },
  short_head_bicep_left: { en: 'Short Head Bicep (L)', ar: 'Short Head Bicep (L)' },
  long_head_bicep_right: { en: 'Long Head Bicep (R)', ar: 'Long Head Bicep (R)' },
  short_head_bicep_right: { en: 'Short Head Bicep (R)', ar: 'Short Head Bicep (R)' },
  wrist_extensors: { en: 'Wrist Extensors', ar: 'Wrist Extensors' },
  wrist_flexors: { en: 'Wrist Flexors', ar: 'Wrist Flexors' },
  hands: { en: 'Hands', ar: 'Hands' },
  abs_up: { en: 'Upper Abdominals', ar: 'Upper Abdominals' },
  abs_down: { en: 'Lower Abdominals', ar: 'Lower Abdominals' },
  outer_quadricep: { en: 'Outer Quadricep', ar: 'Outer Quadricep' },
  inner_quadricep: { en: 'Inner Quadricep', ar: 'Inner Quadricep' },
  inner_thigh: { en: 'Inner Thigh', ar: 'Inner Thigh' },
  feet: { en: 'Feet', ar: 'Feet' },
  groin: { en: 'Groin', ar: 'Groin' },
  long_head_triceps: { en: 'Long Head Triceps', ar: 'Long Head Triceps' },
  lateral_head_triceps: { en: 'Lateral Head Triceps', ar: 'Lateral Head Triceps' },
  medial_head_triceps: { en: 'Medial Head Triceps', ar: 'Medial Head Triceps' },
  long_head_triceps_left: { en: 'Long Head Triceps (L)', ar: 'Long Head Triceps (L)' },
  lateral_head_triceps_left: { en: 'Lateral Head Triceps (L)', ar: 'Lateral Head Triceps (L)' },
  medial_head_triceps_left: { en: 'Medial Head Triceps (L)', ar: 'Medial Head Triceps (L)' },
  long_head_triceps_right: { en: 'Long Head Triceps (R)', ar: 'Long Head Triceps (R)' },
  lateral_head_triceps_right: { en: 'Lateral Head Triceps (R)', ar: 'Lateral Head Triceps (R)' },
  medial_head_triceps_right: { en: 'Medial Head Triceps (R)', ar: 'Medial Head Triceps (R)' },
  lowerback: { en: 'Lower Back', ar: 'Lower Back' },
  medial_hamstrings: { en: 'Medial Hamstrings', ar: 'Medial Hamstrings' },
  lateral_hamstrings: { en: 'Lateral Hamstrings', ar: 'Lateral Hamstrings' },
  upper_chest: { en: 'Upper Chest', ar: 'الصدر العلوي' },
  middle_chest: { en: 'Middle Chest', ar: 'الصدر الأوسط' },
  lower_chest: { en: 'Lower Chest', ar: 'الصدر السفلي' },
  inner_chest: { en: 'Inner Chest', ar: 'الصدر الداخلي' },
  side_delts: { en: 'Side Delts', ar: 'الكتف الجانبي' },
  biceps_long_left: { en: 'Long Head Bicep (L)', ar: 'Long Head Bicep (L)' },
  biceps_short_left: { en: 'Short Head Bicep (L)', ar: 'Short Head Bicep (L)' },
  biceps_long_right: { en: 'Long Head Bicep (R)', ar: 'Long Head Bicep (R)' },
  biceps_short_right: { en: 'Short Head Bicep (R)', ar: 'Short Head Bicep (R)' },
  upper_abs: { en: 'Upper Abdominals', ar: 'Upper Abdominals' },
  middle_abs: { en: 'Middle Abdominals', ar: 'Middle Abdominals' },
  lower_abs: { en: 'Lower Abdominals', ar: 'Lower Abdominals' },
  serratus: { en: 'Serratus', ar: 'المنشارية' },
  rectus_femoris: { en: 'Rectus Femoris', ar: 'العضلة المستقيمة' },
  vastus_lateralis: { en: 'Vastus Lateralis', ar: 'المتسعة الوحشية' },
  vastus_medialis: { en: 'Vastus Medialis', ar: 'المتسعة الإنسية' },
  upper_traps: { en: 'Upper Trapezius', ar: 'Upper Trapezius' },
  middle_traps: { en: 'Traps Middle', ar: 'Traps Middle' },
  lower_traps: { en: 'Lower Trapezius', ar: 'Lower Trapezius' },
  upper_lats: { en: 'Upper Lats', ar: 'مجنص علوي' },
  middle_lats: { en: 'Middle Lats', ar: 'مجنص أوسط' },
  lower_lats: { en: 'Lower Lats', ar: 'مجنص سفلي' },
  teres_major: { en: 'Teres Major', ar: 'المدورة الكبرى' },
  teres_minor: { en: 'Teres Minor', ar: 'المدورة الصغرى' },
  erector_spinae: { en: 'Erector Spinae', ar: 'ناصبة الفقار' },
  triceps_long_left: { en: 'Long Head Triceps (L)', ar: 'Long Head Triceps (L)' },
  triceps_lateral_left: { en: 'Lateral Head Triceps (L)', ar: 'Lateral Head Triceps (L)' },
  triceps_medial_left: { en: 'Medial Head Triceps (L)', ar: 'Medial Head Triceps (L)' },
  triceps_long_right: { en: 'Long Head Triceps (R)', ar: 'Long Head Triceps (R)' },
  triceps_lateral_right: { en: 'Lateral Head Triceps (R)', ar: 'Lateral Head Triceps (R)' },
  triceps_medial_right: { en: 'Medial Head Triceps (R)', ar: 'Medial Head Triceps (R)' },
  gluteus_maximus: { en: 'Gluteus Maximus', ar: 'الألوية الكبرى' },
  gluteus_medius: { en: 'Gluteus Medius', ar: 'الألوية الوسطى' },
  biceps_femoris: { en: 'Biceps Femoris', ar: 'ذات الرأسين الفخذية' },
  semitendinosus: { en: 'Semitendinosus', ar: 'نصف الوترية' },
  semimembranosus: { en: 'Semimembranosus', ar: 'نصف الغشائية' },
  gastrocnemius: { en: 'Gastrocnemius', ar: 'الساقية' },
  soleus: { en: 'Soleus', ar: 'النعلية' },
};

const arabicMuscleFallback: Record<string, string> = {
  upper_pectoralis: 'الصدر العلوي',
  mid_lower_pectoralis: 'الصدر الأوسط والسفلي',
  anterior_deltoid: 'الدالية الأمامية',
  lateral_deltoid: 'الدالية الجانبية',
  posterior_deltoid: 'الدالية الخلفية',
  upper_trapezius: 'الترابيس العلوية',
  traps_middle: 'الترابيس الوسطى',
  lower_trapezius: 'الترابيس السفلية',
  long_head_bicep: 'الرأس الطويل للبايسبس',
  short_head_bicep: 'الرأس القصير للبايسبس',
  long_head_bicep_left: 'الرأس الطويل للبايسبس (يسار)',
  short_head_bicep_left: 'الرأس القصير للبايسبس (يسار)',
  long_head_bicep_right: 'الرأس الطويل للبايسبس (يمين)',
  short_head_bicep_right: 'الرأس القصير للبايسبس (يمين)',
  wrist_extensors: 'باسطات المعصم',
  wrist_flexors: 'قابضات المعصم',
  hands: 'اليدان',
  abs_up: 'البطن العلوي',
  abs_down: 'البطن السفلي',
  outer_quadricep: 'الرباعية الخارجية',
  inner_quadricep: 'الرباعية الداخلية',
  inner_thigh: 'الفخذ الداخلي',
  feet: 'القدمان',
  groin: 'الأربية',
  long_head_triceps: 'الرأس الطويل للترايسبس',
  lateral_head_triceps: 'الرأس الجانبي للترايسبس',
  medial_head_triceps: 'الرأس الإنسي للترايسبس',
  long_head_triceps_left: 'الرأس الطويل للترايسبس (يسار)',
  lateral_head_triceps_left: 'الرأس الجانبي للترايسبس (يسار)',
  medial_head_triceps_left: 'الرأس الإنسي للترايسبس (يسار)',
  long_head_triceps_right: 'الرأس الطويل للترايسبس (يمين)',
  lateral_head_triceps_right: 'الرأس الجانبي للترايسبس (يمين)',
  medial_head_triceps_right: 'الرأس الإنسي للترايسبس (يمين)',
  lowerback: 'أسفل الظهر',
  medial_hamstrings: 'الهامسترنغ الإنسي',
  lateral_hamstrings: 'الهامسترنغ الجانبي',
  biceps_long_left: 'الرأس الطويل للبايسبس (يسار)',
  biceps_short_left: 'الرأس القصير للبايسبس (يسار)',
  biceps_long_right: 'الرأس الطويل للبايسبس (يمين)',
  biceps_short_right: 'الرأس القصير للبايسبس (يمين)',
  upper_abs: 'البطن العلوي',
  middle_abs: 'البطن الأوسط',
  lower_abs: 'البطن السفلي',
  upper_traps: 'الترابيس العلوية',
  middle_traps: 'الترابيس الوسطى',
  lower_traps: 'الترابيس السفلية',
  upper_lats: 'اللاتس العلوية',
  middle_lats: 'اللاتس الوسطى',
  lower_lats: 'اللاتس السفلية',
  triceps_long_left: 'الرأس الطويل للترايسبس (يسار)',
  triceps_lateral_left: 'الرأس الجانبي للترايسبس (يسار)',
  triceps_medial_left: 'الرأس الإنسي للترايسبس (يسار)',
  triceps_long_right: 'الرأس الطويل للترايسبس (يمين)',
  triceps_lateral_right: 'الرأس الجانبي للترايسبس (يمين)',
  triceps_medial_right: 'الرأس الإنسي للترايسبس (يمين)',
};

export { advancedToGroupMap };

export function AnatomyBody({ selectedMuscles, onMuscleToggle, muscleNames }: AnatomyBodyProps) {
  const { profile } = useUser();
  const { language } = useLanguage();
  const [view, setView] = useState<BodyView>('front');
  const [gender, setGender] = useState<BodyGender>(profile?.gender === 'female' ? 'female' : 'male');
  const [level, setLevel] = useState<BodyLevel>('normal');

  const isActive = (muscle: string) => selectedMuscles.includes(muscle);

  const getMuscleStyle = (muscle: string) => {
    const active = isActive(muscle);
    return {
      fill: active ? 'hsl(188, 100%, 48%)' : 'hsl(0, 65%, 55%)',
      stroke: active ? 'hsl(188, 100%, 65%)' : 'hsl(0, 50%, 35%)',
      strokeWidth: active ? 1.5 : 0.7,
      cursor: 'pointer' as const,
      transition: 'all 0.3s ease',
      filter: active ? 'drop-shadow(0 0 12px hsla(188, 100%, 48%, 0.8))' : 'none',
      opacity: active ? 1 : 0.95,
    };
  };

  const outlineColor = 'hsl(0, 45%, 40%)';
  const isFemale = gender === 'female';

  // Get muscle list for sidebar based on level and view
  const getMuscleList = (): string[] => {
    if (level === 'normal') {
      return view === 'front' ? normalFrontMuscles : normalBackMuscles;
    }
    return view === 'front' ? advancedFrontMuscles : advancedBackMuscles;
  };

  const getMuscleLabel = (id: string) => {
    const label = muscleLabels[id];
    const en = repairMojibake(label?.en || id);
    const arRaw = repairMojibake(label?.ar || '');
    const ar = arRaw && arRaw !== en ? arRaw : (arabicMuscleFallback[id] || en);
    return language === 'ar' ? ar : en;
  };

  const assetConfig = level === 'normal'
    ? isFemale
      ? view === 'front'
        ? {
            canvas: FEMALE_FRONT_CANVAS,
            base: femaleFrontBase,
            layers: parsedFemaleFrontNormalLayers,
          }
        : {
            canvas: FEMALE_BACK_CANVAS,
            base: femaleBackBase,
            layers: parsedFemaleBackNormalLayers,
          }
      : view === 'front'
        ? {
            canvas: MALE_FRONT_CANVAS,
            base: maleFrontBase,
            layers: parsedMaleFrontNormalLayers,
          }
        : {
            canvas: MALE_BACK_CANVAS,
            base: maleBackBase,
            layers: parsedMaleBackNormalLayers,
          }
    : level === 'advanced'
      ? isFemale
        ? view === 'front'
          ? {
              canvas: FEMALE_FRONT_ADVANCED_CANVAS,
              base: femaleFrontAdvancedBase,
              layers: parsedFemaleFrontAdvancedLayers,
            }
          : {
              canvas: FEMALE_BACK_ADVANCED_CANVAS,
              base: femaleBackAdvancedBase,
              layers: parsedFemaleBackAdvancedLayers,
            }
        : view === 'front'
          ? {
              canvas: MALE_FRONT_ADVANCED_CANVAS,
              base: maleFrontAdvancedBase,
              layers: parsedMaleFrontAdvancedLayers,
            }
          : {
              canvas: MALE_BACK_ADVANCED_CANVAS,
              base: maleBackAdvancedBase,
              layers: parsedMaleBackAdvancedLayers,
            }
      : null;

  const shouldUseAssetLayers = Boolean(assetConfig);

  const getLayerMuscleList = (layers: ParsedFemaleNormalLayer[]): string[] => {
    const seen = new Set<string>();
    return layers.reduce<string[]>((acc, layer) => {
      if (!seen.has(layer.muscleId)) {
        seen.add(layer.muscleId);
        acc.push(layer.muscleId);
      }
      return acc;
    }, []);
  };

  const renderAssetBody = () => {
    if (!assetConfig) return null;

    return (
      <div className="w-56 h-[30rem] md:w-72 md:h-[38rem] flex items-center justify-center">
        <svg
          viewBox={`0 0 ${assetConfig.canvas.width} ${assetConfig.canvas.height}`}
          className="h-full w-auto max-w-full"
        >
          <image
            href={assetConfig.base}
            x="0"
            y="0"
            width={assetConfig.canvas.width}
            height={assetConfig.canvas.height}
            preserveAspectRatio="none"
          />

          {assetConfig.layers.map((layer) => {
            const layerMuscles = layer.activeMuscles ?? [layer.muscleId];
            const active = layerMuscles.some(isActive);
            const scaleX = layer.width / layer.sourceWidth;
            const scaleY = layer.height / layer.sourceHeight;
            const strokeScale = Math.max(scaleX, scaleY);
            const translateX = layer.x - layer.sourceOffsetX * scaleX;
            const translateY = layer.y - layer.sourceOffsetY * scaleY;

            return layer.pathDs.map((pathD, index) => (
              <path
                key={`${layer.id}-${index}`}
                d={pathD}
                transform={`translate(${translateX} ${translateY}) scale(${scaleX} ${scaleY})`}
                fill={active ? 'hsl(188, 100%, 48%)' : 'hsl(0, 65%, 55%)'}
                stroke={active ? 'hsl(188, 100%, 65%)' : 'hsl(0, 50%, 35%)'}
                strokeWidth={(active ? 1.4 : 0.8) / strokeScale}
                vectorEffect="non-scaling-stroke"
                opacity={active ? 1 : 0.92}
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  filter: active ? 'drop-shadow(0 0 10px hsla(188, 100%, 48%, 0.8))' : 'none',
                }}
                onClick={() => onMuscleToggle(layer.muscleId)}
                aria-label={getMuscleLabel(layer.muscleId)}
              />
            ));
          })}
        </svg>
      </div>
    );
  };

  // Render male front body SVG
  const renderMaleFrontNormal = () => (
    <g>
      {/* Front Delts */}
      <path d="M62,88 Q58,82 68,78 L80,80 Q72,84 68,90 L62,92 Q58,94 58,96 Z"
        style={getMuscleStyle('front_delts')} onClick={() => onMuscleToggle('front_delts')} />
      <path d="M198,88 Q202,82 192,78 L180,80 Q188,84 192,90 L198,92 Q202,94 202,96 Z"
        style={getMuscleStyle('front_delts')} onClick={() => onMuscleToggle('front_delts')} />
      
      {/* Chest */}
      <path d="M86,86 Q108,82 130,86 Q130,100 125,108 Q118,114 108,116 Q98,118 90,112 Q84,106 86,95 Z"
        style={getMuscleStyle('chest')} onClick={() => onMuscleToggle('chest')} />
      <path d="M174,86 Q152,82 130,86 Q130,100 135,108 Q142,114 152,116 Q162,118 170,112 Q176,106 174,95 Z"
        style={getMuscleStyle('chest')} onClick={() => onMuscleToggle('chest')} />

      {/* Biceps */}
      <path d="M54,100 Q48,102 44,110 L40,132 Q38,142 42,148 L50,146 Q54,142 56,132 L60,110 Q62,102 58,98 Z"
        style={getMuscleStyle('biceps')} onClick={() => onMuscleToggle('biceps')} />
      <path d="M206,100 Q212,102 216,110 L220,132 Q222,142 218,148 L210,146 Q206,142 204,132 L200,110 Q198,102 202,98 Z"
        style={getMuscleStyle('biceps')} onClick={() => onMuscleToggle('biceps')} />

      {/* Abs */}
      <g onClick={() => onMuscleToggle('abs')} style={{ cursor: 'pointer' }}>
        <rect x="118" y="120" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
        <rect x="132" y="120" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
        <rect x="118" y="135" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
        <rect x="132" y="135" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
        <rect x="118" y="150" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
        <rect x="132" y="150" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
        <rect x="118" y="165" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
        <rect x="132" y="165" width="10" height="12" rx="2" style={getMuscleStyle('abs')} />
      </g>

      {/* Obliques */}
      <path d="M100,125 Q104,128 108,130 L108,185 Q104,188 100,190 L92,185 Q88,178 86,165 L84,145 Q84,135 88,128 Z"
        style={{ ...getMuscleStyle('obliques'), opacity: isActive('obliques') ? 0.7 : 0.5 }} onClick={() => onMuscleToggle('obliques')} />
      <path d="M160,125 Q156,128 152,130 L152,185 Q156,188 160,190 L168,185 Q172,178 174,165 L176,145 Q176,135 172,128 Z"
        style={{ ...getMuscleStyle('obliques'), opacity: isActive('obliques') ? 0.7 : 0.5 }} onClick={() => onMuscleToggle('obliques')} />

      {/* Quads */}
      <path d="M78,258 Q75,268 72,290 L68,330 Q66,342 70,346 L90,346 Q94,342 92,330 L96,290 Q98,268 95,258 Z"
        style={getMuscleStyle('quads')} onClick={() => onMuscleToggle('quads')} />
      <path d="M182,258 Q185,268 188,290 L192,330 Q194,342 190,346 L170,346 Q166,342 168,330 L164,290 Q162,268 165,258 Z"
        style={getMuscleStyle('quads')} onClick={() => onMuscleToggle('quads')} />

      {/* Adductors */}
      <path d="M98,260 L108,260 Q112,280 118,300 L120,320 Q116,330 110,335 L100,335 Q94,325 92,310 L94,280 Z"
        style={getMuscleStyle('adductors')} onClick={() => onMuscleToggle('adductors')} />
      <path d="M162,260 L152,260 Q148,280 142,300 L140,320 Q144,330 150,335 L160,335 Q166,325 168,310 L166,280 Z"
        style={getMuscleStyle('adductors')} onClick={() => onMuscleToggle('adductors')} />

      {/* Tibialis */}
      <path d="M72,355 Q70,365 70,380 L72,415 Q74,422 78,425 L82,425 Q84,418 84,408 L84,380 Q84,365 82,355 Z"
        style={getMuscleStyle('tibialis')} onClick={() => onMuscleToggle('tibialis')} />
      <path d="M188,355 Q190,365 190,380 L188,415 Q186,422 182,425 L178,425 Q176,418 176,408 L176,380 Q176,365 178,355 Z"
        style={getMuscleStyle('tibialis')} onClick={() => onMuscleToggle('tibialis')} />
    </g>
  );

  const renderMaleBackNormal = () => (
    <g>
      {/* Traps */}
      <path d="M100,82 Q115,78 130,82 Q145,78 160,82 L165,95 Q160,110 155,118 L130,125 L105,118 Q100,110 95,95 Z"
        style={getMuscleStyle('traps')} onClick={() => onMuscleToggle('traps')} />

      {/* Rear Delts */}
      <path d="M62,88 Q58,82 68,78 L80,80 Q72,84 68,90 L62,92 Q58,94 58,96 Z"
        style={getMuscleStyle('rear_delts')} onClick={() => onMuscleToggle('rear_delts')} />
      <path d="M198,88 Q202,82 192,78 L180,80 Q188,84 192,90 L198,92 Q202,94 202,96 Z"
        style={getMuscleStyle('rear_delts')} onClick={() => onMuscleToggle('rear_delts')} />

      {/* Triceps */}
      <path d="M54,100 Q48,102 44,110 L40,132 Q38,142 42,148 L50,146 Q54,142 56,132 L60,110 Q62,102 58,98 Z"
        style={getMuscleStyle('triceps')} onClick={() => onMuscleToggle('triceps')} />
      <path d="M206,100 Q212,102 216,110 L220,132 Q222,142 218,148 L210,146 Q206,142 204,132 L200,110 Q198,102 202,98 Z"
        style={getMuscleStyle('triceps')} onClick={() => onMuscleToggle('triceps')} />

      {/* Lats */}
      <path d="M86,100 Q95,95 105,100 L108,130 Q106,150 100,160 L88,155 Q82,140 82,120 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      <path d="M174,100 Q165,95 155,100 L152,130 Q154,150 160,160 L172,155 Q178,140 178,120 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />

      {/* Lower Back */}
      <path d="M105,155 Q115,150 130,152 Q145,150 155,155 L158,180 Q155,195 150,200 L130,205 L110,200 Q105,195 102,180 Z"
        style={getMuscleStyle('lower_back')} onClick={() => onMuscleToggle('lower_back')} />

      {/* Glutes */}
      <path d="M78,215 Q85,210 100,212 L115,215 Q120,220 118,232 Q115,245 105,250 L85,250 Q75,245 72,232 Q70,220 78,215 Z"
        style={getMuscleStyle('glutes')} onClick={() => onMuscleToggle('glutes')} />
      <path d="M182,215 Q175,210 160,212 L145,215 Q140,220 142,232 Q145,245 155,250 L175,250 Q185,245 188,232 Q190,220 182,215 Z"
        style={getMuscleStyle('glutes')} onClick={() => onMuscleToggle('glutes')} />

      {/* Hamstrings */}
      <path d="M78,258 Q75,268 72,290 L68,330 Q66,342 70,346 L90,346 Q94,342 92,330 L96,290 Q98,268 95,258 Z"
        style={getMuscleStyle('hamstrings')} onClick={() => onMuscleToggle('hamstrings')} />
      <path d="M182,258 Q185,268 188,290 L192,330 Q194,342 190,346 L170,346 Q166,342 168,330 L164,290 Q162,268 165,258 Z"
        style={getMuscleStyle('hamstrings')} onClick={() => onMuscleToggle('hamstrings')} />

      {/* Calves */}
      <path d="M70,355 Q68,365 68,380 L68,415 Q70,425 76,430 L82,430 Q88,425 90,415 L90,380 Q90,365 88,355 Z"
        style={getMuscleStyle('calves')} onClick={() => onMuscleToggle('calves')} />
      <path d="M190,355 Q192,365 192,380 L192,415 Q190,425 184,430 L178,430 Q172,425 170,415 L170,380 Q170,365 172,355 Z"
        style={getMuscleStyle('calves')} onClick={() => onMuscleToggle('calves')} />
    </g>
  );

  // Advanced front muscles
  const renderMaleFrontAdvanced = () => (
    <g>
      {/* Upper Chest */}
      <path d="M88,86 Q108,83 130,86 L130,95 Q120,93 108,94 Q96,95 90,93 Z"
        style={getMuscleStyle('upper_chest')} onClick={() => onMuscleToggle('upper_chest')} />
      <path d="M172,86 Q152,83 130,86 L130,95 Q140,93 152,94 Q164,95 170,93 Z"
        style={getMuscleStyle('upper_chest')} onClick={() => onMuscleToggle('upper_chest')} />
      {/* Middle Chest */}
      <path d="M90,95 Q108,92 130,95 L130,106 Q118,108 108,108 Q96,108 88,104 Z"
        style={getMuscleStyle('middle_chest')} onClick={() => onMuscleToggle('middle_chest')} />
      <path d="M170,95 Q152,92 130,95 L130,106 Q142,108 152,108 Q164,108 172,104 Z"
        style={getMuscleStyle('middle_chest')} onClick={() => onMuscleToggle('middle_chest')} />
      {/* Lower Chest */}
      <path d="M88,106 Q100,110 115,112 L130,108 L130,116 Q118,118 108,116 Q96,115 88,110 Z"
        style={getMuscleStyle('lower_chest')} onClick={() => onMuscleToggle('lower_chest')} />
      <path d="M172,106 Q160,110 145,112 L130,108 L130,116 Q142,118 152,116 Q164,115 172,110 Z"
        style={getMuscleStyle('lower_chest')} onClick={() => onMuscleToggle('lower_chest')} />
      {/* Inner Chest */}
      <rect x="126" y="88" width="8" height="26" rx="2"
        style={getMuscleStyle('inner_chest')} onClick={() => onMuscleToggle('inner_chest')} />

      {/* Front Delts */}
      <path d="M62,88 Q58,82 68,78 L80,80 Q72,84 68,90 L62,92 Q58,94 58,96 Z"
        style={getMuscleStyle('front_delts')} onClick={() => onMuscleToggle('front_delts')} />
      <path d="M198,88 Q202,82 192,78 L180,80 Q188,84 192,90 L198,92 Q202,94 202,96 Z"
        style={getMuscleStyle('front_delts')} onClick={() => onMuscleToggle('front_delts')} />
      {/* Side Delts */}
      <path d="M58,96 Q54,100 52,106 L56,112 Q60,106 64,100 L68,94 Z"
        style={getMuscleStyle('side_delts')} onClick={() => onMuscleToggle('side_delts')} />
      <path d="M202,96 Q206,100 208,106 L204,112 Q200,106 196,100 L192,94 Z"
        style={getMuscleStyle('side_delts')} onClick={() => onMuscleToggle('side_delts')} />

      {/* Biceps Long/Short Left */}
      <path d="M54,102 Q50,106 46,115 L42,135 Q42,142 46,145 L50,143 Q52,138 54,128 L56,112 Z"
        style={getMuscleStyle('biceps_long_left')} onClick={() => onMuscleToggle('biceps_long_left')} />
      <path d="M56,112 Q56,120 56,130 L54,140 Q54,146 58,148 L60,145 Q62,138 62,128 L62,112 Z"
        style={getMuscleStyle('biceps_short_left')} onClick={() => onMuscleToggle('biceps_short_left')} />
      {/* Biceps Long/Short Right */}
      <path d="M206,102 Q210,106 214,115 L218,135 Q218,142 214,145 L210,143 Q208,138 206,128 L204,112 Z"
        style={getMuscleStyle('biceps_long_right')} onClick={() => onMuscleToggle('biceps_long_right')} />
      <path d="M204,112 Q204,120 204,130 L206,140 Q206,146 202,148 L200,145 Q198,138 198,128 L198,112 Z"
        style={getMuscleStyle('biceps_short_right')} onClick={() => onMuscleToggle('biceps_short_right')} />

      {/* Upper Abs */}
      <g onClick={() => onMuscleToggle('upper_abs')} style={{ cursor: 'pointer' }}>
        <rect x="118" y="120" width="10" height="12" rx="2" style={getMuscleStyle('upper_abs')} />
        <rect x="132" y="120" width="10" height="12" rx="2" style={getMuscleStyle('upper_abs')} />
      </g>
      {/* Middle Abs */}
      <g onClick={() => onMuscleToggle('middle_abs')} style={{ cursor: 'pointer' }}>
        <rect x="118" y="135" width="10" height="12" rx="2" style={getMuscleStyle('middle_abs')} />
        <rect x="132" y="135" width="10" height="12" rx="2" style={getMuscleStyle('middle_abs')} />
        <rect x="118" y="150" width="10" height="12" rx="2" style={getMuscleStyle('middle_abs')} />
        <rect x="132" y="150" width="10" height="12" rx="2" style={getMuscleStyle('middle_abs')} />
      </g>
      {/* Lower Abs */}
      <g onClick={() => onMuscleToggle('lower_abs')} style={{ cursor: 'pointer' }}>
        <rect x="118" y="165" width="10" height="12" rx="2" style={getMuscleStyle('lower_abs')} />
        <rect x="132" y="165" width="10" height="12" rx="2" style={getMuscleStyle('lower_abs')} />
      </g>

      {/* Serratus */}
      <path d="M100,118 L108,120 L108,140 L100,138 Q96,132 96,126 Z"
        style={getMuscleStyle('serratus')} onClick={() => onMuscleToggle('serratus')} />
      <path d="M160,118 L152,120 L152,140 L160,138 Q164,132 164,126 Z"
        style={getMuscleStyle('serratus')} onClick={() => onMuscleToggle('serratus')} />

      {/* Obliques */}
      <path d="M100,140 Q104,143 108,145 L108,185 Q104,188 100,190 L92,185 Q88,178 86,165 L84,150 Q86,142 92,138 Z"
        style={{ ...getMuscleStyle('obliques'), opacity: isActive('obliques') ? 0.7 : 0.5 }} onClick={() => onMuscleToggle('obliques')} />
      <path d="M160,140 Q156,143 152,145 L152,185 Q156,188 160,190 L168,185 Q172,178 174,165 L176,150 Q174,142 168,138 Z"
        style={{ ...getMuscleStyle('obliques'), opacity: isActive('obliques') ? 0.7 : 0.5 }} onClick={() => onMuscleToggle('obliques')} />

      {/* Rectus Femoris */}
      <path d="M82,260 Q80,275 78,300 L76,330 Q76,340 80,344 L86,344 Q90,340 88,330 L90,300 Q92,275 90,260 Z"
        style={getMuscleStyle('rectus_femoris')} onClick={() => onMuscleToggle('rectus_femoris')} />
      <path d="M178,260 Q180,275 182,300 L184,330 Q184,340 180,344 L174,344 Q170,340 172,330 L170,300 Q168,275 170,260 Z"
        style={getMuscleStyle('rectus_femoris')} onClick={() => onMuscleToggle('rectus_femoris')} />
      {/* Vastus Lateralis */}
      <path d="M76,260 Q72,275 68,300 L66,330 Q66,340 70,344 L78,344 Q80,340 78,330 L76,300 Q76,275 78,260 Z"
        style={getMuscleStyle('vastus_lateralis')} onClick={() => onMuscleToggle('vastus_lateralis')} />
      <path d="M184,260 Q188,275 192,300 L194,330 Q194,340 190,344 L182,344 Q180,340 182,330 L184,300 Q184,275 182,260 Z"
        style={getMuscleStyle('vastus_lateralis')} onClick={() => onMuscleToggle('vastus_lateralis')} />
      {/* Vastus Medialis */}
      <path d="M92,290 Q96,300 100,315 L102,330 Q100,340 96,344 L90,344 Q88,340 88,330 L90,315 Q90,300 90,290 Z"
        style={getMuscleStyle('vastus_medialis')} onClick={() => onMuscleToggle('vastus_medialis')} />
      <path d="M168,290 Q164,300 160,315 L158,330 Q160,340 164,344 L170,344 Q172,340 172,330 L170,315 Q170,300 170,290 Z"
        style={getMuscleStyle('vastus_medialis')} onClick={() => onMuscleToggle('vastus_medialis')} />
    </g>
  );

const renderMaleBackAdvanced = () => (
  <g>
    {/* Neck */}
    <path d="M118,64 L118,79 Q118,83 122,83 L138,83 Q142,83 142,79 L142,64 Z"
      style={getMuscleStyle('neck')} onClick={() => onMuscleToggle('neck')} />

    {/* Upper Traps */}
    <path d="M105,82 Q118,78 130,82 Q142,78 155,82 L158,92 Q150,88 130,90 Q110,88 102,92 Z"
      style={getMuscleStyle('upper_trapezius')} onClick={() => onMuscleToggle('upper_trapezius')} />
      {/* Middle Traps */}
      <path d="M102,94 Q115,90 130,92 Q145,90 158,94 L160,108 Q148,104 130,106 Q112,104 100,108 Z"
        style={getMuscleStyle('traps_middle')} onClick={() => onMuscleToggle('traps_middle')} />
      {/* Lower Traps */}
      <path d="M100,110 Q115,106 130,108 Q145,106 160,110 L155,125 Q145,120 130,122 Q115,120 105,125 Z"
        style={getMuscleStyle('lower_trapezius')} onClick={() => onMuscleToggle('lower_trapezius')} />

      {/* Rear Delts */}
      <path d="M62,88 Q58,82 68,78 L80,80 Q72,84 68,90 L62,92 Q58,94 58,96 Z"
        style={getMuscleStyle('posterior_deltoid')} onClick={() => onMuscleToggle('posterior_deltoid')} />
      <path d="M198,88 Q202,82 192,78 L180,80 Q188,84 192,90 L198,92 Q202,94 202,96 Z"
        style={getMuscleStyle('posterior_deltoid')} onClick={() => onMuscleToggle('posterior_deltoid')} />

      {/* Triceps Long/Lateral/Medial Left */}
      <path d="M54,100 Q50,104 46,112 L42,132 Q42,138 44,142 L48,140 Q50,135 52,125 L54,112 Z"
        style={getMuscleStyle('long_head_triceps')} onClick={() => onMuscleToggle('long_head_triceps')} />
      <path d="M52,106 Q52,116 52,126 L50,138 Q52,144 56,146 L58,142 Q58,135 58,126 L58,112 Z"
        style={getMuscleStyle('lateral_head_triceps')} onClick={() => onMuscleToggle('lateral_head_triceps')} />
      <path d="M58,114 L62,112 L62,138 Q60,144 56,148 L54,144 Q56,138 56,128 Z"
        style={getMuscleStyle('medial_head_triceps')} onClick={() => onMuscleToggle('medial_head_triceps')} />
      {/* Triceps Long/Lateral/Medial Right */}
      <path d="M206,100 Q210,104 214,112 L218,132 Q218,138 216,142 L212,140 Q210,135 208,125 L206,112 Z"
        style={getMuscleStyle('long_head_triceps')} onClick={() => onMuscleToggle('long_head_triceps')} />
      <path d="M208,106 Q208,116 208,126 L210,138 Q208,144 204,146 L202,142 Q202,135 202,126 L202,112 Z"
        style={getMuscleStyle('lateral_head_triceps')} onClick={() => onMuscleToggle('lateral_head_triceps')} />
      <path d="M202,114 L198,112 L198,138 Q200,144 204,148 L206,144 Q204,138 204,128 Z"
        style={getMuscleStyle('medial_head_triceps')} onClick={() => onMuscleToggle('medial_head_triceps')} />

      {/* Teres Major/Minor */}
      <path d="M86,105 L95,100 L98,115 L88,118 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      <path d="M86,120 L98,117 L100,130 L88,132 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      <path d="M174,105 L165,100 L162,115 L172,118 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      <path d="M174,120 L162,117 L160,130 L172,132 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />

      {/* Upper Lats */}
      <path d="M88,120 Q95,115 105,118 L108,135 Q104,145 98,148 L86,142 Q82,135 84,125 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      <path d="M172,120 Q165,115 155,118 L152,135 Q156,145 162,148 L174,142 Q178,135 176,125 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      {/* Middle Lats */}
      <path d="M86,144 Q95,140 100,148 L102,162 Q98,170 92,172 L84,168 Q80,158 82,148 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      <path d="M174,144 Q165,140 160,148 L158,162 Q162,170 168,172 L176,168 Q180,158 178,148 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      {/* Lower Lats */}
      <path d="M84,170 Q92,168 98,172 L100,185 Q96,192 90,194 L84,190 Q80,182 82,175 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />
      <path d="M176,170 Q168,168 162,172 L160,185 Q164,192 170,194 L176,190 Q180,182 178,175 Z"
        style={getMuscleStyle('lats')} onClick={() => onMuscleToggle('lats')} />

      {/* Erector Spinae */}
      <path d="M120,130 Q125,128 130,130 Q135,128 140,130 L142,195 Q138,202 130,205 Q122,202 118,195 Z"
        style={getMuscleStyle('lower_back')} onClick={() => onMuscleToggle('lower_back')} />

      {/* Gluteus Maximus */}
      <path d="M80,218 Q90,212 105,215 L118,220 Q122,228 120,238 Q116,248 105,252 L85,252 Q76,248 73,238 Q72,225 80,218 Z"
        style={getMuscleStyle('gluteus_maximus')} onClick={() => onMuscleToggle('gluteus_maximus')} />
      <path d="M180,218 Q170,212 155,215 L142,220 Q138,228 140,238 Q144,248 155,252 L175,252 Q184,248 187,238 Q188,225 180,218 Z"
        style={getMuscleStyle('gluteus_maximus')} onClick={() => onMuscleToggle('gluteus_maximus')} />
      {/* Gluteus Medius */}
      <path d="M78,210 Q88,205 100,208 L108,212 L105,215 Q92,212 80,216 L75,214 Z"
        style={getMuscleStyle('gluteus_medius')} onClick={() => onMuscleToggle('gluteus_medius')} />
      <path d="M182,210 Q172,205 160,208 L152,212 L155,215 Q168,212 180,216 L185,214 Z"
        style={getMuscleStyle('gluteus_medius')} onClick={() => onMuscleToggle('gluteus_medius')} />

      {/* Biceps Femoris */}
      <path d="M76,258 Q72,275 68,295 L66,330 Q66,340 70,344 L78,344 Q80,340 78,325 L80,295 Q82,275 80,258 Z"
        style={getMuscleStyle('lateral_hamstrings')} onClick={() => onMuscleToggle('lateral_hamstrings')} />
      <path d="M184,258 Q188,275 192,295 L194,330 Q194,340 190,344 L182,344 Q180,340 182,325 L180,295 Q178,275 180,258 Z"
        style={getMuscleStyle('lateral_hamstrings')} onClick={() => onMuscleToggle('lateral_hamstrings')} />
      {/* Semitendinosus */}
      <path d="M82,260 Q84,275 86,295 L86,330 Q86,340 84,344 L80,344 Q78,340 78,325 L80,295 Q80,275 80,260 Z"
        style={getMuscleStyle('medial_hamstrings')} onClick={() => onMuscleToggle('medial_hamstrings')} />
      <path d="M178,260 Q176,275 174,295 L174,330 Q174,340 176,344 L180,344 Q182,340 182,325 L180,295 Q180,275 180,260 Z"
        style={getMuscleStyle('medial_hamstrings')} onClick={() => onMuscleToggle('medial_hamstrings')} />
      {/* Semimembranosus */}
      <path d="M86,260 Q90,278 92,300 L92,330 Q90,340 88,344 L84,344 Q84,340 86,330 L86,300 Q84,278 84,260 Z"
        style={getMuscleStyle('medial_hamstrings')} onClick={() => onMuscleToggle('medial_hamstrings')} />
      <path d="M174,260 Q170,278 168,300 L168,330 Q170,340 172,344 L176,344 Q176,340 174,330 L174,300 Q176,278 176,260 Z"
        style={getMuscleStyle('medial_hamstrings')} onClick={() => onMuscleToggle('medial_hamstrings')} />

      {/* Gastrocnemius */}
      <path d="M70,355 Q68,365 68,380 L70,410 Q72,420 78,424 L82,420 Q86,412 86,400 L86,380 Q86,365 84,355 Z"
        style={getMuscleStyle('gastrocnemius')} onClick={() => onMuscleToggle('gastrocnemius')} />
      <path d="M190,355 Q192,365 192,380 L190,410 Q188,420 182,424 L178,420 Q174,412 174,400 L174,380 Q174,365 176,355 Z"
        style={getMuscleStyle('gastrocnemius')} onClick={() => onMuscleToggle('gastrocnemius')} />
      {/* Soleus */}
      <path d="M72,425 Q74,430 78,434 L82,434 Q86,430 88,425 L88,440 Q86,446 82,448 L78,448 Q74,446 72,440 Z"
        style={getMuscleStyle('soleus')} onClick={() => onMuscleToggle('soleus')} />
      <path d="M188,425 Q186,430 182,434 L178,434 Q174,430 172,425 L172,440 Q174,446 178,448 L182,448 Q186,446 188,440 Z"
        style={getMuscleStyle('soleus')} onClick={() => onMuscleToggle('soleus')} />
    </g>
  );

  // Body outline differs by gender
  const renderBodyOutline = () => {
    if (isFemale) {
      return (
        <g fill="url(#skinGrad)" stroke={outlineColor} strokeWidth="0.8" strokeLinejoin="round">
          {/* Head - slightly rounder */}
          <ellipse cx="130" cy="38" rx="21" ry="27" />
          {/* Neck - thinner */}
          <path d="M120,63 L120,76 Q120,80 124,80 L136,80 Q140,80 140,76 L140,63" />
          {/* Torso - narrower shoulders, wider hips */}
          <path d="M84,80 Q76,82 72,88 L66,90 Q62,92 62,96 L60,110 Q58,120 60,130 L62,145 
                   Q64,155 66,160 L68,175 L68,190 Q68,198 72,202 L80,210 Q84,214 92,216
                   L130,218 L168,216 Q176,214 180,210 L188,202 Q192,198 192,190 L192,175 
                   L194,160 Q196,155 198,145 L200,130 Q202,120 200,110 L198,96 Q198,92 194,90 
                   L188,88 Q184,82 176,80 Z" />
          {/* Arms - thinner */}
          <path d="M62,92 Q52,95 48,102 L42,125 Q40,138 42,148 Q44,154 48,156 L54,154 Q58,152 60,146 L66,125 Q68,112 66,100 Z" />
          <path d="M198,92 Q208,95 212,102 L218,125 Q220,138 218,148 Q216,154 212,156 L206,154 Q202,152 200,146 L194,125 Q192,112 194,100 Z" />
          {/* Forearms */}
          <path d="M42,156 Q38,160 36,168 L32,196 Q30,206 32,210 L36,213 Q40,215 44,213 L48,210 Q52,206 54,196 L58,168 Q60,160 56,156 Z" />
          <path d="M218,156 Q222,160 224,168 L228,196 Q230,206 228,210 L224,213 Q220,215 216,213 L212,210 Q208,206 206,196 L202,168 Q200,160 204,156 Z" />
          {/* Hands */}
          <ellipse cx="34" cy="220" rx="7" ry="11" />
          <ellipse cx="226" cy="220" rx="7" ry="11" />
          {/* Hips - wider for female */}
          <path d="M80,216 L180,216 Q188,220 192,228 L194,242 Q192,256 186,260 L74,260 Q68,256 66,242 L68,228 Q72,220 80,216 Z" />
          {/* Upper Legs */}
          <path d="M74,260 Q70,266 68,276 L64,335 Q62,348 64,352 L90,352 Q94,348 92,335 L96,276 Q98,266 95,260 Z" />
          <path d="M186,260 Q190,266 192,276 L196,335 Q198,348 196,352 L170,352 Q166,348 168,335 L164,276 Q162,266 165,260 Z" />
          {/* Lower Legs */}
          <path d="M64,352 L90,352 Q92,362 90,375 L88,425 Q86,435 83,440 L71,440 Q68,435 66,425 L64,375 Q62,362 64,352 Z" />
          <path d="M196,352 L170,352 Q168,362 170,375 L172,425 Q174,435 177,440 L189,440 Q192,435 194,425 L196,375 Q198,362 196,352 Z" />
          {/* Feet */}
          <path d="M66,440 L84,440 Q90,443 92,448 L92,456 Q90,462 84,464 L66,464 Q60,462 58,456 L58,448 Q60,443 66,440 Z" />
          <path d="M194,440 L176,440 Q170,443 168,448 L168,456 Q170,462 176,464 L194,464 Q200,462 202,456 L202,448 Q200,443 194,440 Z" />
        </g>
      );
    }
    // Male body
    return (
      <g fill="url(#skinGrad)" stroke={outlineColor} strokeWidth="0.8" strokeLinejoin="round">
        <ellipse cx="130" cy="38" rx="22" ry="28" />
        <path d="M118,64 L118,76 Q118,80 122,80 L138,80 Q142,80 142,76 L142,64" />
        <path d="M80,80 Q72,82 68,88 L62,90 Q58,92 58,96 L56,110 Q54,120 56,130 L58,145 
                 Q60,155 62,160 L65,175 L65,190 Q65,198 70,202 L78,208 Q82,210 88,210
                 L130,210 L172,210 Q178,210 182,208 L190,202 Q195,198 195,190 L195,175 
                 L198,160 Q200,155 202,145 L204,130 Q206,120 204,110 L202,96 Q202,92 198,90 
                 L192,88 Q188,82 180,80 Z" />
        <path d="M58,92 Q48,95 44,102 L38,125 Q36,140 38,150 Q40,156 44,158 L52,156 Q56,154 58,148 L64,125 Q66,112 64,100 Z" />
        <path d="M202,92 Q212,95 216,102 L222,125 Q224,140 222,150 Q220,156 216,158 L208,156 Q204,154 202,148 L196,125 Q194,112 196,100 Z" />
        <path d="M38,158 Q34,162 32,170 L28,200 Q26,210 28,215 L32,218 Q36,220 40,218 L44,215 Q48,210 50,200 L54,170 Q56,162 52,158 Z" />
        <path d="M222,158 Q226,162 228,170 L232,200 Q234,210 232,215 L228,218 Q224,220 220,218 L216,215 Q212,210 210,200 L206,170 Q204,162 208,158 Z" />
        <ellipse cx="30" cy="226" rx="8" ry="12" />
        <ellipse cx="230" cy="226" rx="8" ry="12" />
        <path d="M78,210 L182,210 Q188,215 190,222 L192,235 Q190,248 185,252 L75,252 Q70,248 68,235 L70,222 Q72,215 78,210 Z" />
        <path d="M75,252 Q72,258 70,268 L66,330 Q64,345 66,348 L92,348 Q96,345 94,330 L98,268 Q100,258 97,252 Z" />
        <path d="M185,252 Q188,258 190,268 L194,330 Q196,345 194,348 L168,348 Q164,345 166,330 L162,268 Q160,258 163,252 Z" />
        <path d="M66,348 L92,348 Q94,358 92,372 L90,425 Q88,435 85,440 L73,440 Q70,435 68,425 L66,372 Q64,358 66,348 Z" />
        <path d="M194,348 L168,348 Q166,358 168,372 L170,425 Q172,435 175,440 L187,440 Q190,435 192,425 L194,372 Q196,358 194,348 Z" />
        <path d="M68,440 L86,440 Q92,443 94,448 L94,456 Q92,462 86,464 L68,464 Q62,462 60,456 L60,448 Q62,443 68,440 Z" />
        <path d="M192,440 L174,440 Q168,443 166,448 L166,456 Q168,462 174,464 L192,464 Q198,462 200,456 L200,448 Q198,443 192,440 Z" />
      </g>
    );
  };

  // For female, we use same muscle paths but slightly adjusted positions
  // The key difference is the body outline. Muscle overlays remain similar.
  const renderFrontMuscles = () => {
    if (level === 'advanced') return renderMaleFrontAdvanced();
    return renderMaleFrontNormal();
  };

  const renderBackMuscles = () => {
    if (level === 'advanced') return renderMaleBackAdvanced();
    return renderMaleBackNormal();
  };

  const muscleList = shouldUseAssetLayers && assetConfig
    ? getLayerMuscleList(assetConfig.layers)
    : getMuscleList();

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Controls Row */}
      <div className="flex flex-wrap gap-3 justify-center">
        {/* View Toggle */}
        <div className="flex bg-card/80 rounded-xl p-1 gap-1 border border-border/50">
          <button onClick={() => setView('front')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              view === 'front' ? 'bg-primary text-primary-foreground shadow-glow' : 'text-muted-foreground hover:text-foreground'
            }`}>
            {language === 'ar' ? 'أمام' : 'Front'}
          </button>
          <button onClick={() => setView('back')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              view === 'back' ? 'bg-primary text-primary-foreground shadow-glow' : 'text-muted-foreground hover:text-foreground'
            }`}>
            {language === 'ar' ? 'خلف' : 'Back'}
          </button>
        </div>

        {/* Gender Toggle */}
        <div className="flex bg-card/80 rounded-xl p-1 gap-1 border border-border/50">
          <button onClick={() => setGender('male')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              gender === 'male' ? 'bg-primary text-primary-foreground shadow-glow' : 'text-muted-foreground hover:text-foreground'
            }`}>
            {language === 'ar' ? 'ذكر' : 'Male'}
          </button>
          <button onClick={() => setGender('female')}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              gender === 'female' ? 'bg-primary text-primary-foreground shadow-glow' : 'text-muted-foreground hover:text-foreground'
            }`}>
            {language === 'ar' ? 'أنثى' : 'Female'}
          </button>
        </div>

        {/* Level Toggle */}
        <div className="flex bg-card/80 rounded-xl p-1 gap-1 border border-border/50">
          <button onClick={() => { setLevel('normal'); }}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              level === 'normal' ? 'bg-primary text-primary-foreground shadow-glow' : 'text-muted-foreground hover:text-foreground'
            }`}>
            {language === 'ar' ? 'عادي' : 'Normal'}
          </button>
          <button onClick={() => { setLevel('advanced'); }}
            className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              level === 'advanced' ? 'bg-primary text-primary-foreground shadow-glow' : 'text-muted-foreground hover:text-foreground'
            }`}>
            {language === 'ar' ? 'متقدم' : 'Advanced'}
          </button>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8 items-center justify-center">
        {/* Anatomy SVG */}
        <div className="relative">
          {shouldUseAssetLayers ? (
            renderAssetBody()
          ) : (
          <svg viewBox="0 0 260 520" className="w-56 h-[30rem] md:w-72 md:h-[38rem]">
            <defs>
              <linearGradient id="skinGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={isFemale ? "hsl(20, 35%, 88%)" : "hsl(25, 30%, 85%)"} />
                <stop offset="100%" stopColor={isFemale ? "hsl(20, 30%, 78%)" : "hsl(25, 25%, 75%)"} />
              </linearGradient>
              <filter id="muscleGlow">
                <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Body Outline */}
            {renderBodyOutline()}

            {/* Muscle fiber detail lines */}
            <g fill="none" stroke={outlineColor} strokeWidth="0.4" opacity="0.4">
              {view === 'front' && (
                <>
                  <path d="M90,95 Q110,92 130,95" />
                  <path d="M130,95 Q150,92 170,95" />
                  <line x1="130" y1="120" x2="130" y2="190" />
                  <line x1="115" y1="125" x2="115" y2="185" />
                  <line x1="145" y1="125" x2="145" y2="185" />
                  <line x1="108" y1="130" x2="152" y2="130" />
                  <line x1="108" y1="145" x2="152" y2="145" />
                  <line x1="108" y1="160" x2="152" y2="160" />
                  <line x1="108" y1="175" x2="152" y2="175" />
                </>
              )}
              {view === 'back' && (
                <>
                  <path d="M90,90 Q110,88 130,92 Q150,88 170,90" />
                  <path d="M95,100 Q110,95 130,98 Q150,95 165,100" />
                  <line x1="130" y1="85" x2="130" y2="200" />
                  <path d="M85,225 Q100,232 115,225" />
                  <path d="M145,225 Q160,232 175,225" />
                </>
              )}
            </g>

            {/* Muscle Overlays */}
            {view === 'front' ? renderFrontMuscles() : renderBackMuscles()}
          </svg>
          )}
        </div>

        {/* Muscle Selection Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 gap-2 w-full lg:w-auto max-h-[32rem] overflow-y-auto scrollbar-thin">
          {muscleList.map((muscleId) => (
            <motion.button
              key={muscleId}
              onClick={() => onMuscleToggle(muscleId)}
              whileTap={{ scale: 0.95 }}
              className={`px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 border ${
                selectedMuscles.includes(muscleId)
                  ? 'bg-primary/15 text-primary border-primary/40 shadow-glow'
                  : 'bg-card/50 text-foreground border-border/30 hover:bg-card/80 hover:border-border/60'
              }`}
            >
              <span className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full transition-all ${
                  selectedMuscles.includes(muscleId) ? 'bg-primary shadow-glow' : 'bg-muted-foreground/30'
                }`} />
                {getMuscleLabel(muscleId)}
              </span>
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
}

