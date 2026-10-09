export interface ShortLink {
    code: string;
    short_url: string;
    original_url: string;
    click_count: number;
    created_at: string;
    expires_at: string | null;
  }
  
  export interface CreateLinkRequest {
    url: string;
    custom_alias: string | null;
    expires_in_days: number | null;
  }
  
  export interface CountItem {
    label: string;
    count: number;
  }
  
  export interface Analytics {
    code: string;
    short_url: string;
    original_url: string;
    total_clicks: number;
    clicks_by_day: CountItem[];
    devices: CountItem[];
    browsers: CountItem[];
    referrers: CountItem[];
  }