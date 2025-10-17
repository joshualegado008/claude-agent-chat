/**
 * Agent Selector Component - Displays selected agents and allows user approval
 */

import { AgentProfile, AgentSelectionMetadata } from '@/types';
import { Check, X, Bot, Sparkles } from 'lucide-react';

interface AgentSelectorProps {
  agents: AgentProfile[];
  metadata: AgentSelectionMetadata;
  onApprove: () => void;
  onReject: () => void;
  isLoading?: boolean;
}

export function AgentSelector({
  agents,
  metadata,
  onApprove,
  onReject,
  isLoading = false,
}: AgentSelectorProps) {
  return (
    <div className="bg-slate-800 rounded-xl shadow-lg border border-slate-700 p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2 flex items-center space-x-2">
          <Bot className="w-6 h-6 text-chorus-primary" />
          <span>Selected Agents for This Conversation</span>
        </h2>
        <p className="text-slate-400 text-sm">
          Review the {agents.length} expert agent{agents.length !== 1 ? 's' : ''} that will discuss this topic
        </p>
      </div>

      {/* Refined Topic */}
      {metadata.refined_topic && (
        <div className="mb-6 p-4 bg-chorus-secondary/20 border border-chorus-secondary rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Sparkles className="w-4 h-4 text-chorus-primary" />
            <span className="text-sm font-medium text-chorus-accent">Enhanced Topic</span>
          </div>
          <p className="text-chorus-light italic">"{metadata.refined_topic}"</p>
        </div>
      )}

      {/* Agent Cards */}
      <div className="space-y-4 mb-6">
        {agents.map((agent, index) => (
          <div
            key={agent.agent_id}
            className="bg-slate-700/50 border border-slate-600 rounded-lg p-4 hover:border-chorus-primary transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="text-3xl">{agent.domain_icon}</div>
                <div>
                  <h3 className="font-bold text-lg">{agent.name}</h3>
                  <p className="text-sm text-slate-400">
                    {agent.domain.charAt(0).toUpperCase() + agent.domain.slice(1)} Expert
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500">Agent #{index + 1}</span>
              </div>
            </div>

            {/* Taxonomy Hierarchy */}
            <div className="mb-3 text-sm">
              <span className="text-slate-400">Classification:</span>{' '}
              <span className="text-slate-200">
                {agent.domain.charAt(0).toUpperCase() + agent.domain.slice(1)} → {agent.primary_class} → {agent.specialization}
              </span>
            </div>

            {/* Expertise */}
            <div className="mb-3">
              <p className="text-sm text-slate-400 mb-1">Expertise:</p>
              <p className="text-slate-200">{agent.unique_expertise}</p>
            </div>

            {/* Core Skills */}
            <div>
              <p className="text-sm text-slate-400 mb-1">Core Skills:</p>
              <div className="flex flex-wrap gap-2">
                {agent.core_skills.slice(0, 5).map((skill) => (
                  <span
                    key={skill}
                    className="px-2 py-1 bg-chorus-secondary/30 text-chorus-accent rounded text-xs border border-chorus-secondary"
                  >
                    {skill}
                  </span>
                ))}
                {agent.core_skills.length > 5 && (
                  <span className="px-2 py-1 bg-slate-600 text-slate-400 rounded text-xs">
                    +{agent.core_skills.length - 5} more
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Metadata Footer */}
      <div className="mb-6 p-4 bg-slate-700/30 rounded-lg border border-slate-600">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-slate-400">Agents Created</p>
            <p className="font-bold text-green-400">{metadata.agents_created}</p>
          </div>
          <div>
            <p className="text-slate-400">Agents Reused</p>
            <p className="font-bold text-blue-400">{metadata.agents_reused}</p>
          </div>
          <div>
            <p className="text-slate-400">Creation Cost</p>
            <p className="font-bold text-amber-400">${metadata.creation_cost.toFixed(4)}</p>
          </div>
          <div>
            <p className="text-slate-400">Cache Savings</p>
            <p className="font-bold text-purple-400">${metadata.cache_savings.toFixed(4)}</p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end space-x-4">
        <button
          onClick={onReject}
          disabled={isLoading}
          className="flex items-center space-x-2 px-6 py-3 bg-slate-700 text-slate-300 rounded-lg font-medium hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-slate-600"
        >
          <X className="w-5 h-5" />
          <span>Cancel</span>
        </button>
        <button
          onClick={onApprove}
          disabled={isLoading}
          className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-chorus-secondary to-chorus-primary text-white rounded-lg font-medium hover:from-chorus-primary hover:to-chorus-accent transition-all duration-200 transform hover:scale-105 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          <Check className="w-5 h-5" />
          <span>{isLoading ? 'Creating...' : 'Approve & Start Conversation'}</span>
        </button>
      </div>
    </div>
  );
}
