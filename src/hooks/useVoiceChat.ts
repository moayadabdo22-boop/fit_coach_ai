import { useCallback, useEffect, useRef, useState } from 'react';

export interface VoiceChatApiResponse {
  transcript: string;
  reply: string;
  audio_path: string;
  conversation_id: string;
  language: string;
}

interface UseVoiceChatOptions {
  backendUrl: string;
  language: 'en' | 'ar';
  userId?: string | null;
  conversationId?: string | null;
  onResponse: (payload: VoiceChatApiResponse) => void | Promise<void>;
}

const CANDIDATE_MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/mp4',
];

export function useVoiceChat({
  backendUrl,
  language,
  userId,
  conversationId,
  onResponse,
}: UseVoiceChatOptions) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const isSupported =
    typeof window !== 'undefined' &&
    typeof navigator !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof MediaRecorder !== 'undefined';

  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const uploadRecording = useCallback(
    async (blob: Blob) => {
      setIsProcessing(true);
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      try {
        const formData = new FormData();
        formData.append('audio', blob, 'voice_input.webm');
        formData.append('language', language);
        if (userId) formData.append('user_id', userId);
        if (conversationId) formData.append('conversation_id', conversationId);

        const response = await fetch(`${backendUrl}/voice-chat`, {
          method: 'POST',
          body: formData,
          signal: abortRef.current.signal,
        });

        if (!response.ok) {
          let details = '';
          try {
            const errPayload = await response.json();
            details = String(errPayload?.detail || '');
          } catch {
            details = await response.text();
          }
          throw new Error(details || `Voice chat failed (${response.status})`);
        }

        const payload = (await response.json()) as VoiceChatApiResponse;
        await onResponse(payload);
      } catch (err: any) {
        if (err?.name === 'AbortError') {
          return;
        }
        console.error('Voice upload error:', err);
        setError(
          language === 'ar'
            ? `فشل إرسال الصوت: ${err?.message || 'خطأ غير معروف'}`
            : `Voice request failed: ${err?.message || 'Unknown error'}`
        );
      } finally {
        setIsProcessing(false);
      }
    },
    [backendUrl, conversationId, language, onResponse, userId]
  );

  const startListening = useCallback(async () => {
    if (!isSupported) {
      setError(
        language === 'ar'
          ? 'المتصفح لا يدعم التسجيل الصوتي.'
          : 'This browser does not support voice recording.'
      );
      return;
    }

    if (isListening || isProcessing) return;
    setError(null);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = CANDIDATE_MIME_TYPES.find((type) => {
        try {
          return MediaRecorder.isTypeSupported(type);
        } catch {
          return false;
        }
      });

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError(
          language === 'ar'
            ? 'حدث خطأ أثناء التسجيل الصوتي.'
            : 'Audio recording failed.'
        );
        setIsListening(false);
        cleanupStream();
      };

      recorder.onstop = async () => {
        const outputType = recorder.mimeType || 'audio/webm';
        const recordedBlob = new Blob(chunksRef.current, { type: outputType });
        chunksRef.current = [];
        setIsListening(false);
        cleanupStream();

        if (recordedBlob.size === 0) {
          setError(
            language === 'ar'
              ? 'لم يتم تسجيل صوت. حاول مرة أخرى.'
              : 'No audio captured. Please try again.'
          );
          return;
        }

        await uploadRecording(recordedBlob);
      };

      recorder.start();
      setIsListening(true);
    } catch (err) {
      console.error('Mic start error:', err);
      cleanupStream();
      setIsListening(false);
      setError(
        language === 'ar'
          ? 'تعذر بدء المايكروفون. تحقق من إذن الميكروفون ثم أعد المحاولة.'
          : 'Could not start microphone. Check permission and retry.'
      );
    }
  }, [cleanupStream, isListening, isProcessing, isSupported, language, uploadRecording]);

  const stopListening = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop();
    } else {
      setIsListening(false);
      cleanupStream();
    }
  }, [cleanupStream]);

  const cancelVoiceRequest = useCallback(() => {
    abortRef.current?.abort();
    setIsProcessing(false);
  }, []);

  useEffect(() => {
    return () => {
      try {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop();
        }
      } catch {
        // no-op cleanup
      }
      cleanupStream();
      abortRef.current?.abort();
    };
  }, [cleanupStream]);

  return {
    isListening,
    isProcessing,
    isSupported,
    error,
    clearError,
    startListening,
    stopListening,
    cancelVoiceRequest,
  };
}

