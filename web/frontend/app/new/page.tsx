'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, Send, Loader2, Tag, X } from 'lucide-react';
import { useGeneratePrompt, useCreateConversation } from '@/hooks/useConversations';
import { Loading } from '@/components/Loading';

export default function NewConversationPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [generatedPrompt, setGeneratedPrompt] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [showPromptPreview, setShowPromptPreview] = useState(false);

  const generatePromptMutation = useGeneratePrompt();
  const createConversationMutation = useCreateConversation();

  const handleGeneratePrompt = async () => {
    if (!title.trim()) return;

    try {
      const result = await generatePromptMutation.mutateAsync(title);
      setGeneratedPrompt(result.generated_prompt);
      setTags(result.suggested_tags || []);
      setShowPromptPreview(true);
    } catch (error: any) {
      console.error('Failed to generate prompt:', error);

      // Show specific error message if available
      let errorMessage = 'Failed to generate prompt. ';
      if (error?.message) {
        errorMessage += error.message;
      } else if (error?.status === 503) {
        errorMessage += 'AI generation service is unavailable. Please enter the prompt manually.';
      } else {
        errorMessage += 'Please try again or enter the prompt manually.';
      }

      alert(errorMessage);
    }
  };

  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  const handleStartConversation = async () => {
    if (!title.trim()) {
      alert('Please enter a title');
      return;
    }

    if (!generatedPrompt.trim()) {
      alert('Please generate a prompt first');
      return;
    }

    try {
      const result = await createConversationMutation.mutateAsync({
        title: title.trim(),
        initial_prompt: generatedPrompt.trim(),
        tags,
        generate_prompt: false, // Already generated
      });

      // Navigate to live conversation page
      router.push(`/conversation/${result.id}`);
    } catch (error) {
      console.error('Failed to create conversation:', error);
      alert('Failed to create conversation. Please try again.');
    }
  };

  const isLoading = generatePromptMutation.isPending || createConversationMutation.isPending;

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
            Start a New Conversation
          </h1>
          <p className="text-slate-400">
            Watch two AI agents discuss any topic in real-time
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-slate-800 rounded-2xl shadow-xl p-8 space-y-6 border border-slate-700">
          {/* Step 1: Title */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">
              Conversation Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., The Future of AI in Healthcare"
              className="w-full px-4 py-3 border border-slate-600 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-slate-700 text-slate-100 placeholder-slate-400"
              disabled={isLoading}
            />
          </div>

          {/* Step 2: Generate Prompt Button */}
          <div>
            <button
              onClick={handleGeneratePrompt}
              disabled={!title.trim() || isLoading}
              className="w-full flex items-center justify-center space-x-2 px-6 py-4 bg-gradient-to-r from-cyan-600 to-purple-600 text-white rounded-lg font-medium hover:from-cyan-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02]"
            >
              {generatePromptMutation.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Generating with AI...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  <span>Generate Prompt & Tags with AI</span>
                </>
              )}
            </button>
          </div>

          {/* Step 3: Prompt Preview */}
          {showPromptPreview && generatedPrompt && (
            <div className="space-y-2 fade-in">
              <label className="block text-sm font-medium text-slate-300">
                Generated Prompt
              </label>
              <textarea
                value={generatedPrompt}
                onChange={(e) => setGeneratedPrompt(e.target.value)}
                rows={6}
                className="w-full px-4 py-3 border border-slate-600 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-slate-700 text-slate-100 resize-none"
                disabled={isLoading}
              />
              <p className="text-xs text-slate-400">
                ✨ AI-generated prompt. Feel free to edit it!
              </p>
            </div>
          )}

          {/* Step 4: Tags */}
          {showPromptPreview && (
            <div className="space-y-2 fade-in">
              <label className="block text-sm font-medium text-slate-300">
                Tags (optional)
              </label>

              {/* Existing Tags */}
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-2">
                  {tags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center space-x-1 px-3 py-1 bg-cyan-900/50 text-cyan-300 rounded-full text-sm border border-cyan-700"
                    >
                      <Tag className="w-3 h-3" />
                      <span>{tag}</span>
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-cyan-200"
                        disabled={isLoading}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {/* Add New Tag */}
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder="Add a tag..."
                  className="flex-1 px-3 py-2 border border-slate-600 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-slate-700 text-slate-100 placeholder-slate-400 text-sm"
                  disabled={isLoading}
                />
                <button
                  onClick={handleAddTag}
                  disabled={!newTag.trim() || isLoading}
                  className="px-4 py-2 bg-slate-600 text-slate-200 rounded-lg hover:bg-slate-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                >
                  Add
                </button>
              </div>
            </div>
          )}

          {/* Step 5: Start Conversation Button */}
          {showPromptPreview && (
            <div className="pt-4 fade-in">
              <button
                onClick={handleStartConversation}
                disabled={!generatedPrompt.trim() || isLoading}
                className="w-full flex items-center justify-center space-x-2 px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg font-bold text-lg hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] shadow-lg"
              >
                {createConversationMutation.isPending ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span>Starting Conversation...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-6 h-6" />
                    <span>Start Conversation</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Back Link */}
        <div className="text-center mt-6">
          <button
            onClick={() => router.push('/')}
            className="text-slate-400 hover:text-slate-200 transition-colors"
            disabled={isLoading}
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
