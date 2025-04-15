export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  marketContext?: any;
  knowledgeContext?: any[];
}

export interface QueryResponse {
  status: string;
  response: string;
  market_context?: any;
  knowledge_context?: any[];
}

export interface InitializeTickerResponse {
  status: string;
  message: string;
  market_context: any;
  options_context: any;
} 
