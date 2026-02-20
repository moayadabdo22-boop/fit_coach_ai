import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useLanguage } from '@/contexts/LanguageContext';
import { CheckCircle2, XCircle, Clock } from 'lucide-react';

interface AIWorkoutPlan {
  id: string;
  name: string;
  duration_days: number;
  exercises: string[];
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  approved_at?: string;
}

interface AINutritionPlan {
  id: string;
  daily_calories: number;
  meals: Array<{ name: string; macros: { protein: number; carbs: number; fat: number } }>;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
}

interface PlanApprovalUIProps {
  type: 'workout' | 'nutrition';
  plan: AIWorkoutPlan | AINutritionPlan;
  onApprove: (planId: string) => Promise<void>;
  onReject: (planId: string) => Promise<void>;
}

export function PlanApprovalUI({
  type,
  plan,
  onApprove,
  onReject,
}: PlanApprovalUIProps) {
  const { t, language } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const [showApproveDialog, setShowApproveDialog] = useState(false);

  const isArabic = language.startsWith('ar');

  const handleApprove = async () => {
    setIsLoading(true);
    try {
      await onApprove(plan.id);
      setShowApproveDialog(false);
    } catch (error) {
      console.error('Approval failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = async () => {
    setIsLoading(true);
    try {
      await onReject(plan.id);
    } catch (error) {
      console.error('Rejection failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (type === 'workout') {
    const workoutPlan = plan as AIWorkoutPlan;
    return (
      <div className="p-4 border rounded-lg bg-blue-50 dark:bg-blue-900/20 space-y-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold">{workoutPlan.name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {workoutPlan.duration_days} days · {workoutPlan.exercises.length} exercises
            </p>
          </div>
          <StatusBadge status={workoutPlan.status} isArabic={isArabic} />
        </div>

        <div>
          <p className="text-sm font-medium mb-2">
            {isArabic ? 'التمارين:' : 'Exercises:'}
          </p>
          <div className="flex flex-wrap gap-2">
            {workoutPlan.exercises.slice(0, 5).map((ex, i) => (
              <span
                key={i}
                className="text-xs bg-blue-200 dark:bg-blue-800 px-2 py-1 rounded"
              >
                {ex}
              </span>
            ))}
            {workoutPlan.exercises.length > 5 && (
              <span className="text-xs text-gray-600">
                +{workoutPlan.exercises.length - 5} more
              </span>
            )}
          </div>
        </div>

        {workoutPlan.status === 'pending' && (
          <div className="flex gap-2">
            <Button
              onClick={() => setShowApproveDialog(true)}
              className="bg-green-600 hover:bg-green-700"
              disabled={isLoading}
            >
              {isArabic ? 'وافق' : 'Approve'}
            </Button>
            <Button
              onClick={handleReject}
              variant="outline"
              disabled={isLoading}
            >
              {isArabic ? 'رفض' : 'Reject'}
            </Button>
          </div>
        )}

        <ApprovalConfirmDialog
          type="workout"
          isOpen={showApproveDialog}
          onOpen={setShowApproveDialog}
          onConfirm={handleApprove}
          isLoading={isLoading}
          isArabic={isArabic}
          planName={workoutPlan.name}
        />
      </div>
    );
  }

  if (type === 'nutrition') {
    const nutritionPlan = plan as AINutritionPlan;
    return (
      <div className="p-4 border rounded-lg bg-green-50 dark:bg-green-900/20 space-y-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold">
              {isArabic ? 'خطة التغذية' : 'Nutrition Plan'}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {nutritionPlan.daily_calories} kcal/day · {nutritionPlan.meals.length} meals
            </p>
          </div>
          <StatusBadge status={nutritionPlan.status} isArabic={isArabic} />
        </div>

        <div>
          <p className="text-sm font-medium mb-2">
            {isArabic ? 'الوجبات:' : 'Meals:'}
          </p>
          <div className="grid grid-cols-1 gap-2">
            {nutritionPlan.meals.slice(0, 3).map((meal, i) => (
              <div
                key={i}
                className="text-sm bg-white dark:bg-slate-800 p-2 rounded flex justify-between"
              >
                <span>{meal.name}</span>
                <span className="text-xs text-gray-600">
                  P:{meal.macros.protein} C:{meal.macros.carbs} F:{meal.macros.fat}
                </span>
              </div>
            ))}
          </div>
        </div>

        {nutritionPlan.status === 'pending' && (
          <div className="flex gap-2">
            <Button
              onClick={() => setShowApproveDialog(true)}
              className="bg-green-600 hover:bg-green-700"
              disabled={isLoading}
            >
              {isArabic ? 'وافق' : 'Approve'}
            </Button>
            <Button
              onClick={handleReject}
              variant="outline"
              disabled={isLoading}
            >
              {isArabic ? 'رفض' : 'Reject'}
            </Button>
          </div>
        )}

        <ApprovalConfirmDialog
          type="nutrition"
          isOpen={showApproveDialog}
          onOpen={setShowApproveDialog}
          onConfirm={handleApprove}
          isLoading={isLoading}
          isArabic={isArabic}
          planName={isArabic ? 'خطة التغذية' : 'Nutrition Plan'}
        />
      </div>
    );
  }

  return null;
}

function StatusBadge({ status, isArabic }: { status: string; isArabic: boolean }) {
  const statusText = {
    pending: isArabic ? 'قيد الانتظار' : 'Pending',
    approved: isArabic ? 'موافق عليه' : 'Approved',
    rejected: isArabic ? 'مرفوض' : 'Rejected',
  };

  const statusBg = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${statusBg[status as keyof typeof statusBg]}`}>
      {statusText[status as keyof typeof statusText]}
    </span>
  );
}

function ApprovalConfirmDialog({
  type,
  isOpen,
  onOpen,
  onConfirm,
  isLoading,
  isArabic,
  planName,
}: {
  type: 'workout' | 'nutrition';
  isOpen: boolean;
  onOpen: (open: boolean) => void;
  onConfirm: () => Promise<void>;
  isLoading: boolean;
  isArabic: boolean;
  planName: string;
}) {
  return (
    <AlertDialog open={isOpen} onOpenChange={onOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {isArabic ? 'تأكيد الموافقة' : 'Confirm Approval'}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {isArabic
              ? `هل تريد الموافقة على ${planName}؟ ستبدأ بتنفيذ هذه الخطة.`
              : `Are you sure you want to approve the ${planName}? This will start your plan.`}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <div className="flex gap-3">
          <AlertDialogCancel disabled={isLoading}>
            {isArabic ? 'إلغاء' : 'Cancel'}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isLoading}
            className="bg-green-600 hover:bg-green-700"
          >
            {isLoading
              ? isArabic
                ? 'جاري...'
                : 'Approving...'
              : isArabic
                ? 'وافق'
                : 'Approve'}
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
