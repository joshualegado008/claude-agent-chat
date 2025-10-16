'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, Send, Loader2, Tag, X, Users } from 'lucide-react';
import { useGeneratePrompt, useCreateConversation, useSelectAgents } from '@/hooks/useConversations';
import { Loading } from '@/components/Loading';
import { AgentSelector } from '@/components/AgentSelector';
import type { AgentProfile, AgentSelectionMetadata } from '@/types';

export default function NewConversationPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [generatedPrompt, setGeneratedPrompt] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [showPromptPreview, setShowPromptPreview] = useState(false);
  const [selectedAgents, setSelectedAgents] = useState<AgentProfile[] | null>(null);
  const [agentMetadata, setAgentMetadata] = useState<AgentSelectionMetadata | null>(null);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [agentProgress, setAgentProgress] = useState<string>('');
  const [isSelectingAgents, setIsSelectingAgents] = useState(false);

  const generatePromptMutation = useGeneratePrompt();
  const selectAgentsMutation = useSelectAgents();
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

  const handleSelectAgents = async () => {
    if (!title.trim()) return;

    setIsSelectingAgents(true);
    setAgentProgress('Starting agent selection...');

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const eventSource = new EventSource(`${API_URL}/api/agents/select-stream?topic=${encodeURIComponent(title)}`);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'start':
            setAgentProgress('Starting agent selection...');
            break;
          case 'refining_topic':
            setAgentProgress('🔍 Refining topic...');
            break;
          case 'topic_refined':
            setAgentProgress('✅ Topic refined');
            break;
          case 'analyzing_expertise':
            setAgentProgress('🧠 Analyzing expertise requirements...');
            break;
          case 'expertise_analyzed':
            setAgentProgress(`✅ Found ${data.count} expertise areas needed`);
            break;
          case 'checking_agent':
            setAgentProgress(`🔍 Checking agent ${data.current}/${data.total}...`);
            break;
          case 'agent_reused':
            setAgentProgress(`♻️ Reusing: ${data.agent_name} (${data.current}/${data.total})`);
            break;
          case 'creating_agent':
            setAgentProgress(`🔮 Creating agent ${data.current}/${data.total}...`);
            break;
          case 'agent_created':
            setAgentProgress(`✅ Created: ${data.agent_name} - ${data.class} (${data.current}/${data.total})`);
            break;
          case 'complete':
            setSelectedAgents(data.agents);
            setAgentMetadata(data.metadata);
            setShowAgentSelector(true);
            setIsSelectingAgents(false);
            setAgentProgress('');
            eventSource.close();
            break;
          case 'error':
            console.error('Agent selection error:', data.message);
            alert(`Failed to select agents: ${data.message}`);
            setIsSelectingAgents(false);
            setAgentProgress('');
            eventSource.close();
            break;
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        alert('Failed to connect to agent selection service. Please try again.');
        setIsSelectingAgents(false);
        setAgentProgress('');
        eventSource.close();
      };

    } catch (error: any) {
      console.error('Failed to select agents:', error);
      alert('Failed to select agents. Please try again.');
      setIsSelectingAgents(false);
      setAgentProgress('');
    }
  };

  const handleApproveAgents = () => {
    // Agent approved - proceed to conversation creation
    handleStartConversation();
  };

  const handleRejectAgents = () => {
    // User rejected agents - reset selection
    setSelectedAgents(null);
    setAgentMetadata(null);
    setShowAgentSelector(false);
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
      // Prepare conversation data
      const conversationData: any = {
        title: title.trim(),
        initial_prompt: generatedPrompt.trim(),
        tags,
        generate_prompt: false, // Already generated
      };

      // Include selected agent IDs if available
      if (selectedAgents && selectedAgents.length >= 2) {
        conversationData.agent_ids = selectedAgents.map(agent => agent.agent_id);
      }

      const result = await createConversationMutation.mutateAsync(conversationData);

      // Navigate to live conversation page
      router.push(`/conversation/${result.id}`);
    } catch (error) {
      console.error('Failed to create conversation:', error);
      alert('Failed to create conversation. Please try again.');
    }
  };

  const isLoading = generatePromptMutation.isPending || isSelectingAgents || createConversationMutation.isPending;

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

          {/* Step 5: Select Agents Button */}
          {showPromptPreview && !showAgentSelector && (
            <div className="pt-4 fade-in">
              {isSelectingAgents && agentProgress && (
                <div className="mb-4 p-4 bg-purple-900/20 border border-purple-700 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
                    <p className="text-purple-200 font-medium">{agentProgress}</p>
                  </div>
                </div>
              )}
              <button
                onClick={handleSelectAgents}
                disabled={!generatedPrompt.trim() || isLoading}
                className="w-full flex items-center justify-center space-x-2 px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-bold text-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02] shadow-lg"
              >
                {isSelectingAgents ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span>Selecting Experts...</span>
                  </>
                ) : (
                  <>
                    <Users className="w-6 h-6" />
                    <span>Select Expert Agents</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Step 6: Agent Selector */}
        {showAgentSelector && selectedAgents && agentMetadata && (
          <div className="mt-6 fade-in">
            <AgentSelector
              agents={selectedAgents}
              metadata={agentMetadata}
              onApprove={handleApproveAgents}
              onReject={handleRejectAgents}
              isLoading={createConversationMutation.isPending}
            />
          </div>
        )}

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
