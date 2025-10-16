'use client';

import { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  BookOpen,
  Lightbulb,
  Users,
  Sparkles,
  MapPin,
  FileText,
  TrendingUp,
  Clock,
  DollarSign,
  Brain,
  MessageCircle
} from 'lucide-react';
import type { ConversationSummary } from '@/types';

interface Props {
  summary: ConversationSummary;
  conversationTitle: string;
  onClose?: () => void;
}

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function CollapsibleSection({ title, icon, children, defaultOpen = false }: SectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-slate-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-slate-800 hover:bg-slate-750 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <div className="text-cyan-400">{icon}</div>
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
        {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
      </button>

      {isOpen && <div className="p-6 bg-slate-850">{children}</div>}
    </div>
  );
}

export function ConversationSummaryDisplay({ summary, conversationTitle, onClose }: Props) {
  const summaryData = summary.summary_data;
  const metadata = summaryData.generation_metadata;

  return (
    <div className="min-h-screen bg-slate-900 py-8">
      <div className="container mx-auto px-4 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold">Conversation Intelligence Report</h1>
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
              >
                Close
              </button>
            )}
          </div>
          <p className="text-slate-400">{conversationTitle}</p>

          {/* TL;DR Banner */}
          <div className="mt-6 p-6 bg-gradient-to-r from-cyan-900/30 to-blue-900/30 border border-cyan-700/50 rounded-lg">
            <div className="flex items-start space-x-3">
              <Sparkles className="w-6 h-6 text-cyan-400 flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-xl font-bold mb-2 text-cyan-300">TL;DR</h2>
                <p className="text-lg leading-relaxed">{summaryData.tldr}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {/* Executive Summary */}
          <CollapsibleSection
            title="Executive Summary"
            icon={<FileText className="w-5 h-5" />}
            defaultOpen={true}
          >
            <p className="text-lg leading-relaxed">{summaryData.executive_summary}</p>
          </CollapsibleSection>

          {/* Key Insights */}
          {summaryData.key_insights && summaryData.key_insights.length > 0 && (
            <CollapsibleSection
              title="Key Insights & Emergent Ideas"
              icon={<Lightbulb className="w-5 h-5" />}
              defaultOpen={true}
            >
              <div className="space-y-4">
                {summaryData.key_insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className="border-l-4 border-cyan-500 pl-4 py-2 bg-slate-800/50 rounded-r"
                  >
                    <h4 className="font-semibold text-cyan-300 mb-2">{insight.insight}</h4>
                    <p className="text-sm text-slate-300 mb-2">{insight.significance}</p>
                    {insight.emerged_at_turn && (
                      <span className="text-xs text-slate-500">Emerged at turn {insight.emerged_at_turn}</span>
                    )}
                  </div>
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* Technical Glossary */}
          {summaryData.technical_glossary && summaryData.technical_glossary.length > 0 && (
            <CollapsibleSection
              title="Technical Glossary"
              icon={<BookOpen className="w-5 h-5" />}
            >
              <div className="space-y-4">
                {summaryData.technical_glossary.map((term, idx) => (
                  <div key={idx} className="border-b border-slate-700 last:border-0 pb-4 last:pb-0">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-cyan-400 text-lg">{term.term}</h4>
                      <span className="text-xs px-2 py-1 bg-slate-700 rounded">
                        {term.difficulty}
                      </span>
                    </div>
                    {term.pronunciation && (
                      <p className="text-sm text-slate-500 italic mb-2">Pronunciation: {term.pronunciation}</p>
                    )}
                    <p className="text-sm mb-2">{term.definition}</p>
                    {term.context && (
                      <p className="text-xs text-slate-400 italic">Context: {term.context}</p>
                    )}
                  </div>
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* Vocabulary Highlights */}
          {summaryData.vocabulary_highlights && summaryData.vocabulary_highlights.length > 0 && (
            <CollapsibleSection
              title="Vocabulary Highlights"
              icon={<Brain className="w-5 h-5" />}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {summaryData.vocabulary_highlights.map((word, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-slate-800 rounded-lg border border-slate-700"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-semibold text-lg text-cyan-300">{word.word}</h4>
                      {word.pronunciation && (
                        <span className="text-xs text-slate-500 italic">{word.pronunciation}</span>
                      )}
                    </div>
                    <p className="text-sm mb-2">{word.definition}</p>
                    {word.usage_example && (
                      <p className="text-xs text-slate-400 italic mb-2">
                        Example: "{word.usage_example}"
                      </p>
                    )}
                    {word.why_interesting && (
                      <p className="text-xs text-cyan-500">{word.why_interesting}</p>
                    )}
                  </div>
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* Agent Contributions */}
          {summaryData.agent_contributions && summaryData.agent_contributions.length > 0 && (
            <CollapsibleSection
              title="Agent Contribution Analysis"
              icon={<Users className="w-5 h-5" />}
              defaultOpen={true}
            >
              <div className="space-y-4">
                {summaryData.agent_contributions.map((agent, idx) => (
                  <div
                    key={idx}
                    className="p-5 bg-slate-800 rounded-lg border border-slate-700"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-xl text-cyan-300">{agent.agent_name}</h4>
                        <p className="text-sm text-slate-400">{agent.qualification}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-500">{agent.turn_count} turns</p>
                        <span
                          className={`text-xs px-2 py-1 rounded ${
                            agent.engagement_level === 'high'
                              ? 'bg-green-900/50 text-green-300'
                              : agent.engagement_level === 'medium'
                              ? 'bg-yellow-900/50 text-yellow-300'
                              : 'bg-slate-700 text-slate-400'
                          }`}
                        >
                          {agent.engagement_level} engagement
                        </span>
                      </div>
                    </div>

                    {agent.communication_style && (
                      <p className="text-sm text-slate-300 mb-3 italic">{agent.communication_style}</p>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                      {agent.key_concepts && agent.key_concepts.length > 0 && (
                        <div>
                          <p className="font-medium text-cyan-400 mb-1">Key Concepts:</p>
                          <ul className="list-disc list-inside text-slate-300 space-y-1">
                            {agent.key_concepts.map((concept, i) => (
                              <li key={i}>{concept}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {agent.technical_terms_introduced && agent.technical_terms_introduced.length > 0 && (
                        <div>
                          <p className="font-medium text-cyan-400 mb-1">Technical Terms:</p>
                          <ul className="list-disc list-inside text-slate-300 space-y-1">
                            {agent.technical_terms_introduced.map((term, i) => (
                              <li key={i}>{term}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {agent.novel_insights && agent.novel_insights.length > 0 && (
                        <div className="md:col-span-2">
                          <p className="font-medium text-cyan-400 mb-1">Novel Insights:</p>
                          <ul className="list-disc list-inside text-slate-300 space-y-1">
                            {agent.novel_insights.map((insight, i) => (
                              <li key={i}>{insight}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {agent.sources_cited && agent.sources_cited.length > 0 && (
                        <div className="md:col-span-2">
                          <p className="font-medium text-cyan-400 mb-1">Sources Cited:</p>
                          <ul className="list-disc list-inside text-slate-300 space-y-1">
                            {agent.sources_cited.map((source, i) => (
                              <li key={i}>{source}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CollapsibleSection>
          )}

          {/* Collaboration Dynamics */}
          {summaryData.collaboration_dynamics && (
            <CollapsibleSection
              title="Collaboration Dynamics"
              icon={<MessageCircle className="w-5 h-5" />}
            >
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="p-3 bg-slate-800 rounded border border-slate-700">
                    <p className="text-xs text-slate-400 mb-1">Overall Quality</p>
                    <p className="text-lg font-semibold capitalize">
                      {summaryData.collaboration_dynamics.overall_quality}
                    </p>
                  </div>
                  <div className="p-3 bg-slate-800 rounded border border-slate-700">
                    <p className="text-xs text-slate-400 mb-1">Interaction Pattern</p>
                    <p className="text-lg font-semibold capitalize">
                      {summaryData.collaboration_dynamics.interaction_pattern}
                    </p>
                  </div>
                </div>

                {summaryData.collaboration_dynamics.friendliest_agent && (
                  <div className="p-4 bg-green-900/20 border border-green-700/50 rounded-lg">
                    <p className="text-sm text-green-300 mb-1">🤝 Most Collaborative Agent</p>
                    <p className="text-lg font-semibold">{summaryData.collaboration_dynamics.friendliest_agent}</p>
                  </div>
                )}

                {summaryData.collaboration_dynamics.most_collaborative_moments &&
                  summaryData.collaboration_dynamics.most_collaborative_moments.length > 0 && (
                    <div>
                      <p className="font-medium text-cyan-400 mb-2">Collaborative Highlights:</p>
                      <div className="space-y-2">
                        {summaryData.collaboration_dynamics.most_collaborative_moments.map((moment, idx) => (
                          <div key={idx} className="p-3 bg-slate-800 rounded border-l-4 border-cyan-500">
                            <p className="text-xs text-slate-500 mb-1">Turns {moment.turn_range}</p>
                            <p className="text-sm">{moment.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {summaryData.collaboration_dynamics.points_of_convergence &&
                    summaryData.collaboration_dynamics.points_of_convergence.length > 0 && (
                      <div>
                        <p className="font-medium text-green-400 mb-2">Points of Agreement:</p>
                        <ul className="list-disc list-inside text-sm space-y-1">
                          {summaryData.collaboration_dynamics.points_of_convergence.map((point, i) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                  {summaryData.collaboration_dynamics.points_of_divergence &&
                    summaryData.collaboration_dynamics.points_of_divergence.length > 0 && (
                      <div>
                        <p className="font-medium text-orange-400 mb-2">Points of Debate:</p>
                        <ul className="list-disc list-inside text-sm space-y-1">
                          {summaryData.collaboration_dynamics.points_of_divergence.map((point, i) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              </div>
            </CollapsibleSection>
          )}

          {/* Named Entities */}
          {summaryData.named_entities && (
            <CollapsibleSection
              title="Named Entities & References"
              icon={<MapPin className="w-5 h-5" />}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {summaryData.named_entities.people && summaryData.named_entities.people.length > 0 && (
                  <div>
                    <p className="font-medium text-cyan-400 mb-2">People:</p>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      {summaryData.named_entities.people.map((person, i) => (
                        <li key={i}>{person}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {summaryData.named_entities.organizations &&
                  summaryData.named_entities.organizations.length > 0 && (
                    <div>
                      <p className="font-medium text-cyan-400 mb-2">Organizations:</p>
                      <ul className="list-disc list-inside text-sm space-y-1">
                        {summaryData.named_entities.organizations.map((org, i) => (
                          <li key={i}>{org}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                {summaryData.named_entities.locations && summaryData.named_entities.locations.length > 0 && (
                  <div>
                    <p className="font-medium text-cyan-400 mb-2">Locations:</p>
                    <ul className="list-disc list-inside text-sm space-y-1">
                      {summaryData.named_entities.locations.map((loc, i) => (
                        <li key={i}>{loc}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {summaryData.named_entities.publications &&
                  summaryData.named_entities.publications.length > 0 && (
                    <div>
                      <p className="font-medium text-cyan-400 mb-2">Publications:</p>
                      <ul className="list-disc list-inside text-sm space-y-1">
                        {summaryData.named_entities.publications.map((pub, i) => (
                          <li key={i}>{pub}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                {summaryData.named_entities.urls && summaryData.named_entities.urls.length > 0 && (
                  <div className="md:col-span-2">
                    <p className="font-medium text-cyan-400 mb-2">URLs Referenced:</p>
                    <ul className="space-y-1">
                      {summaryData.named_entities.urls.map((url, i) => (
                        <li key={i}>
                          <a
                            href={url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-400 hover:underline"
                          >
                            {url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </CollapsibleSection>
          )}

          {/* Learning Outcomes */}
          {summaryData.learning_outcomes && summaryData.learning_outcomes.length > 0 && (
            <CollapsibleSection
              title="Learning Outcomes"
              icon={<TrendingUp className="w-5 h-5" />}
            >
              <ul className="space-y-3">
                {summaryData.learning_outcomes.map((outcome, idx) => (
                  <li key={idx} className="flex items-start space-x-3">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span>{outcome}</span>
                  </li>
                ))}
              </ul>
            </CollapsibleSection>
          )}

          {/* Generation Metadata */}
          <div className="p-6 bg-slate-800 border border-slate-700 rounded-lg">
            <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
              <FileText className="w-5 h-5 text-cyan-400" />
              <span>Summary Generation Metadata</span>
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-slate-400 mb-1">Model</p>
                <p className="font-semibold">{summary.generation_model}</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1">Tokens Used</p>
                <p className="font-semibold">{summary.total_tokens.toLocaleString()}</p>
                <p className="text-xs text-slate-500">
                  {summary.input_tokens.toLocaleString()} in / {summary.output_tokens.toLocaleString()} out
                </p>
              </div>
              <div>
                <p className="text-slate-400 mb-1 flex items-center space-x-1">
                  <DollarSign className="w-3 h-3" />
                  <span>Cost</span>
                </p>
                <p className="font-semibold">${summary.generation_cost.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-slate-400 mb-1 flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>Time</span>
                </p>
                <p className="font-semibold">{(summary.generation_time_ms / 1000).toFixed(2)}s</p>
              </div>
            </div>

            {metadata?.conversation_stats && (
              <div className="mt-4 pt-4 border-t border-slate-700">
                <p className="text-xs text-slate-500 mb-2">Conversation Statistics:</p>
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div>
                    <p className="text-slate-400">Total Turns</p>
                    <p className="font-semibold">{metadata.conversation_stats.total_turns}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Conversation Tokens</p>
                    <p className="font-semibold">{metadata.conversation_stats.total_tokens.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Combined Cost</p>
                    <p className="font-semibold">${metadata.conversation_stats.combined_cost.toFixed(4)}</p>
                  </div>
                </div>
              </div>
            )}

            <p className="text-xs text-slate-500 mt-4 italic">
              Generated at {new Date(summary.generated_at).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
