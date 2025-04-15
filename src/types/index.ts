export interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
  timestamp: number;
  loading?: boolean;
  marketContext?: any;
  knowledgeContext?: any;
}

export interface MarketData {
  price: number;
  volume: number;
  timestamp: string;
  bid?: number;
  ask?: number;
  bid_size?: number;
  ask_size?: number;
  market_cap?: number;
  rsi?: number;
  macd?: number;
  volume_ma?: number;
}

export interface DailyData {
  dates: string[];
  prices: number[];
  volumes: number[];
}

export interface TechnicalIndicators {
  sma_20: number[];
  sma_50: number[];
  rsi: number[];
  macd: {
    macd: number[];
    signal: number[];
    histogram: number[];
  };
  volume_ma: number[];
}

export interface MarketContext {
  symbol: string;
  current_data: MarketData;
  daily_data: DailyData;
  high_52_week?: number;
  low_52_week?: number;
}

export interface OptionsContract {
  id: string;
  symbol: string;
  name: string;
  status: string;
  tradable: boolean;
  expiration_date: string;
  root_symbol: string;
  underlying_symbol: string;
  underlying_asset_id: string;
  type: 'call' | 'put';
  style: 'american' | 'european';
  strike_price: string;
  multiplier: string;
  size: string;
  open_interest: string;
  open_interest_date: string;
  close_price: string;
  close_price_date: string;
  ppind: boolean;
}

export interface KnowledgeContext {
  company_name: string;
  description: string;
  sector: string;
  industry: string;
  employees: number;
  website: string;
  market_cap: number;
  pe_ratio: number;
  beta: number;
  dividend_yield: number;
  current_price: number;
  contracts: OptionsContract[];
}

export interface AnalysisContext {
  market: MarketContext;
  knowledge: KnowledgeContext;
}

export interface QueryResponse {
  status: string;
  response: string;
  market_context: MarketContext;
  knowledge_context: KnowledgeContext;
}

export interface InitializeTickerResponse {
  status: string;
  message: string;
  market_context: MarketContext;
  options_context: KnowledgeContext;
}

export interface ChatState {
  messages: Message[];
  loading: boolean;
  error: string | null;
  context: AnalysisContext | null;
}

export interface ChatActions {
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setContext: (context: AnalysisContext) => void;
  clearMessages: () => void;
}

export interface ChatStore extends ChatState {
  actions: ChatActions;
}

export interface OptionsContext {
  symbol: string;
  contracts: OptionsContract[];
  timestamp: string;
  error?: string;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    borderColor: string;
    backgroundColor: string;
    fill?: boolean;
    tension?: number;
    pointRadius?: number;
    yAxisID?: string;
  }[];
} 
