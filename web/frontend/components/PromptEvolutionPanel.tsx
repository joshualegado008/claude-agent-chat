'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Sparkles, User, Brain } from 'lucide-react';
import type { PromptMetadata } from '@/types';

interface PromptEvolutionPanelProps {
  metadata: PromptMetadata;
}

export function PromptEvolutionPanel({ metadata }: PromptEvolutionPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Check if we have any evolution data to show
  const hasEvolution = !!(
    metadata.generated_title ||
    metadata.generated_prompt ||
    metadata.refined_topic ||
    metadata.expertise_requirements
  );

  if (!hasEvolution) {
    // If no AI enhancements were made, don't show the panel
    return null;
  }

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      {/* Header - Always visible, clickable to expand */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-750 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span className="font-medium text-slate-200">
            Prompt Evolution
          </span>
          <span className="text-xs text-slate-400">
            (View how AI enhanced your request)
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        )}
      </button>

      {/* Expandable Content */}
      {isExpanded && (
        <div className="px-4 py-4 space-y-4 border-t border-slate-700">
          {/* Step 1: Original User Input */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <User className="w-4 h-4 text-cyan-400" />
              <h4 className="font-medium text-sm text-slate-300">
                1. Your Original Request
              </h4>
            </div>
            <div className="pl-6 p-3 bg-slate-900/50 rounded border border-slate-600">
              <p className="text-slate-200 text-sm">
                {metadata.original_user_input}
              </p>
            </div>
          </div>

          {/* Step 2: AI-Enhanced Prompt (GPT-4o-mini) */}
          {metadata.generated_prompt && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-green-400" />
                <h4 className="font-medium text-sm text-slate-300">
                  2. AI-Enhanced Discussion Prompt
                </h4>
                <span className="text-xs text-slate-500">
                  (GPT-4o-mini)
                </span>
              </div>
              <div className="pl-6 p-3 bg-green-900/10 rounded border border-green-700/30">
                <p className="text-slate-200 text-sm">
                  {metadata.generated_prompt}
                </p>
              </div>
              {metadata.timestamps?.prompt_generated_at && (
                <p className="pl-6 text-xs text-slate-500">
                  Generated: {new Date(metadata.timestamps.prompt_generated_at).toLocaleString()}
                </p>
              )}
            </div>
          )}

          {/* Step 3: Title Refinement */}
          {metadata.generated_title && metadata.generated_title !== metadata.original_user_input && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-blue-400" />
                <h4 className="font-medium text-sm text-slate-300">
                  Concise Title Generated
                </h4>
              </div>
              <div className="pl-6 p-3 bg-blue-900/10 rounded border border-blue-700/30">
                <p className="text-slate-200 text-sm">
                  {metadata.generated_title}
                </p>
              </div>
            </div>
          )}

          {/* Step 4: Agent Selection Analysis (Sonnet) */}
          {(metadata.refined_topic || metadata.expertise_requirements) && (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Brain className="w-4 h-4 text-purple-400" />
                <h4 className="font-medium text-sm text-slate-300">
                  3. Agent Selection Analysis
                </h4>
                <span className="text-xs text-slate-500">
                  (Claude Sonnet)
                </span>
              </div>
              <div className="pl-6 space-y-3">
                {metadata.refined_topic && (
                  <div className="p-3 bg-purple-900/10 rounded border border-purple-700/30">
                    <p className="text-xs text-purple-300 font-medium mb-1">
                      Refined Topic:
                    </p>
                    <p className="text-slate-200 text-sm">
                      {metadata.refined_topic}
                    </p>
                  </div>
                )}
                {metadata.expertise_requirements && metadata.expertise_requirements.length > 0 && (
                  <div className="p-3 bg-purple-900/10 rounded border border-purple-700/30">
                    <p className="text-xs text-purple-300 font-medium mb-2">
                      Expertise Requirements:
                    </p>
                    <ul className="space-y-1">
                      {metadata.expertise_requirements.map((expertise, idx) => (
                        <li key={idx} className="text-slate-200 text-sm flex items-start">
                          <span className="text-purple-400 mr-2">•</span>
                          <span>{expertise}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {metadata.timestamps?.topic_refined_at && (
                  <p className="text-xs text-slate-500">
                    Analyzed: {new Date(metadata.timestamps.topic_refined_at).toLocaleString()}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Info footer */}
          <div className="pt-3 border-t border-slate-700">
            <p className="text-xs text-slate-500">
              This shows how your original request was enhanced by AI to create an engaging, focused discussion between specialized agents.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
