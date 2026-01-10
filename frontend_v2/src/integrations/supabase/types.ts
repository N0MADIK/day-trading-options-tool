export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.1"
  }
  public: {
    Tables: {
      connected_accounts: {
        Row: {
          account_name: string | null
          account_number_masked: string | null
          balance: number | null
          connection_status: string | null
          created_at: string
          currency: string | null
          id: string
          institution_name: string
          institution_type: string
          is_connected: boolean | null
          last_synced_at: string | null
          metadata: Json | null
          updated_at: string
          user_id: string
        }
        Insert: {
          account_name?: string | null
          account_number_masked?: string | null
          balance?: number | null
          connection_status?: string | null
          created_at?: string
          currency?: string | null
          id?: string
          institution_name: string
          institution_type: string
          is_connected?: boolean | null
          last_synced_at?: string | null
          metadata?: Json | null
          updated_at?: string
          user_id: string
        }
        Update: {
          account_name?: string | null
          account_number_masked?: string | null
          balance?: number | null
          connection_status?: string | null
          created_at?: string
          currency?: string | null
          id?: string
          institution_name?: string
          institution_type?: string
          is_connected?: boolean | null
          last_synced_at?: string | null
          metadata?: Json | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      custom_notification_rules: {
        Row: {
          conditions: Json
          created_at: string
          frequency: string
          id: string
          indicator_type: string | null
          is_enabled: boolean | null
          last_triggered_at: string | null
          notify_email: boolean | null
          notify_push: boolean | null
          notify_sms: boolean | null
          quiet_hours_end: string | null
          quiet_hours_start: string | null
          rule_name: string
          rule_type: string
          sensitivity: number | null
          trigger_count: number | null
          updated_at: string
          urgency_level: string
          user_id: string
        }
        Insert: {
          conditions?: Json
          created_at?: string
          frequency?: string
          id?: string
          indicator_type?: string | null
          is_enabled?: boolean | null
          last_triggered_at?: string | null
          notify_email?: boolean | null
          notify_push?: boolean | null
          notify_sms?: boolean | null
          quiet_hours_end?: string | null
          quiet_hours_start?: string | null
          rule_name: string
          rule_type: string
          sensitivity?: number | null
          trigger_count?: number | null
          updated_at?: string
          urgency_level?: string
          user_id: string
        }
        Update: {
          conditions?: Json
          created_at?: string
          frequency?: string
          id?: string
          indicator_type?: string | null
          is_enabled?: boolean | null
          last_triggered_at?: string | null
          notify_email?: boolean | null
          notify_push?: boolean | null
          notify_sms?: boolean | null
          quiet_hours_end?: string | null
          quiet_hours_start?: string | null
          rule_name?: string
          rule_type?: string
          sensitivity?: number | null
          trigger_count?: number | null
          updated_at?: string
          urgency_level?: string
          user_id?: string
        }
        Relationships: []
      }
      holdings: {
        Row: {
          account_id: string | null
          asset_type: string | null
          average_cost: number | null
          created_at: string
          current_price: number | null
          id: string
          market_value: number | null
          name: string | null
          quantity: number
          symbol: string
          unrealized_pnl: number | null
          unrealized_pnl_percent: number | null
          updated_at: string
          user_id: string
        }
        Insert: {
          account_id?: string | null
          asset_type?: string | null
          average_cost?: number | null
          created_at?: string
          current_price?: number | null
          id?: string
          market_value?: number | null
          name?: string | null
          quantity: number
          symbol: string
          unrealized_pnl?: number | null
          unrealized_pnl_percent?: number | null
          updated_at?: string
          user_id: string
        }
        Update: {
          account_id?: string | null
          asset_type?: string | null
          average_cost?: number | null
          created_at?: string
          current_price?: number | null
          id?: string
          market_value?: number | null
          name?: string | null
          quantity?: number
          symbol?: string
          unrealized_pnl?: number | null
          unrealized_pnl_percent?: number | null
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "holdings_account_id_fkey"
            columns: ["account_id"]
            isOneToOne: false
            referencedRelation: "connected_accounts"
            referencedColumns: ["id"]
          },
        ]
      }
      market_data_subscriptions: {
        Row: {
          api_key_encrypted: string | null
          created_at: string
          expires_at: string | null
          features: Json | null
          id: string
          is_active: boolean | null
          provider_name: string
          provider_type: string
          subscription_tier: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          api_key_encrypted?: string | null
          created_at?: string
          expires_at?: string | null
          features?: Json | null
          id?: string
          is_active?: boolean | null
          provider_name: string
          provider_type: string
          subscription_tier?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          api_key_encrypted?: string | null
          created_at?: string
          expires_at?: string | null
          features?: Json | null
          id?: string
          is_active?: boolean | null
          provider_name?: string
          provider_type?: string
          subscription_tier?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      net_worth_goals: {
        Row: {
          created_at: string
          id: string
          last_notified_at: string | null
          notify_on_progress: boolean | null
          notify_threshold_percent: number | null
          target_amount: number
          target_date: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          last_notified_at?: string | null
          notify_on_progress?: boolean | null
          notify_threshold_percent?: number | null
          target_amount: number
          target_date?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          last_notified_at?: string | null
          notify_on_progress?: boolean | null
          notify_threshold_percent?: number | null
          target_amount?: number
          target_date?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      net_worth_history: {
        Row: {
          breakdown: Json | null
          id: string
          recorded_at: string
          total_assets: number
          total_liabilities: number | null
          total_net_worth: number
          user_id: string
        }
        Insert: {
          breakdown?: Json | null
          id?: string
          recorded_at?: string
          total_assets: number
          total_liabilities?: number | null
          total_net_worth: number
          user_id: string
        }
        Update: {
          breakdown?: Json | null
          id?: string
          recorded_at?: string
          total_assets?: number
          total_liabilities?: number | null
          total_net_worth?: number
          user_id?: string
        }
        Relationships: []
      }
      notification_settings: {
        Row: {
          created_at: string
          daily_summary: boolean | null
          email_notifications: boolean | null
          goal_progress_alerts: boolean | null
          id: string
          price_alerts: boolean | null
          push_notifications: boolean | null
          updated_at: string
          user_id: string
          weekly_reports: boolean | null
        }
        Insert: {
          created_at?: string
          daily_summary?: boolean | null
          email_notifications?: boolean | null
          goal_progress_alerts?: boolean | null
          id?: string
          price_alerts?: boolean | null
          push_notifications?: boolean | null
          updated_at?: string
          user_id: string
          weekly_reports?: boolean | null
        }
        Update: {
          created_at?: string
          daily_summary?: boolean | null
          email_notifications?: boolean | null
          goal_progress_alerts?: boolean | null
          id?: string
          price_alerts?: boolean | null
          push_notifications?: boolean | null
          updated_at?: string
          user_id?: string
          weekly_reports?: boolean | null
        }
        Relationships: []
      }
      profiles: {
        Row: {
          address: string | null
          avatar_url: string | null
          created_at: string
          date_of_birth: string | null
          email: string | null
          full_name: string | null
          id: string
          phone: string | null
          subscription_tier: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          address?: string | null
          avatar_url?: string | null
          created_at?: string
          date_of_birth?: string | null
          email?: string | null
          full_name?: string | null
          id?: string
          phone?: string | null
          subscription_tier?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          address?: string | null
          avatar_url?: string | null
          created_at?: string
          date_of_birth?: string | null
          email?: string | null
          full_name?: string | null
          id?: string
          phone?: string | null
          subscription_tier?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      trading_strategies: {
        Row: {
          account_id: string | null
          configuration: Json | null
          created_at: string
          data_subscription_id: string | null
          description: string | null
          id: string
          is_active: boolean | null
          is_automated: boolean | null
          last_executed_at: string | null
          name: string
          next_execution_at: string | null
          schedule: Json | null
          strategy_type: string
          updated_at: string
          user_id: string
        }
        Insert: {
          account_id?: string | null
          configuration?: Json | null
          created_at?: string
          data_subscription_id?: string | null
          description?: string | null
          id?: string
          is_active?: boolean | null
          is_automated?: boolean | null
          last_executed_at?: string | null
          name: string
          next_execution_at?: string | null
          schedule?: Json | null
          strategy_type: string
          updated_at?: string
          user_id: string
        }
        Update: {
          account_id?: string | null
          configuration?: Json | null
          created_at?: string
          data_subscription_id?: string | null
          description?: string | null
          id?: string
          is_active?: boolean | null
          is_automated?: boolean | null
          last_executed_at?: string | null
          name?: string
          next_execution_at?: string | null
          schedule?: Json | null
          strategy_type?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "trading_strategies_account_id_fkey"
            columns: ["account_id"]
            isOneToOne: false
            referencedRelation: "connected_accounts"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "trading_strategies_data_subscription_id_fkey"
            columns: ["data_subscription_id"]
            isOneToOne: false
            referencedRelation: "market_data_subscriptions"
            referencedColumns: ["id"]
          },
        ]
      }
      transactions: {
        Row: {
          account_id: string | null
          created_at: string
          description: string | null
          fees: number | null
          id: string
          price: number | null
          quantity: number | null
          symbol: string | null
          total_amount: number
          transaction_date: string
          transaction_type: string
          user_id: string
        }
        Insert: {
          account_id?: string | null
          created_at?: string
          description?: string | null
          fees?: number | null
          id?: string
          price?: number | null
          quantity?: number | null
          symbol?: string | null
          total_amount: number
          transaction_date: string
          transaction_type: string
          user_id: string
        }
        Update: {
          account_id?: string | null
          created_at?: string
          description?: string | null
          fees?: number | null
          id?: string
          price?: number | null
          quantity?: number | null
          symbol?: string | null
          total_amount?: number
          transaction_date?: string
          transaction_type?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "transactions_account_id_fkey"
            columns: ["account_id"]
            isOneToOne: false
            referencedRelation: "connected_accounts"
            referencedColumns: ["id"]
          },
        ]
      }
      user_roles: {
        Row: {
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
      }
      watchlist: {
        Row: {
          created_at: string
          id: string
          name: string | null
          notes: string | null
          price_alert_above: number | null
          price_alert_below: number | null
          symbol: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          name?: string | null
          notes?: string | null
          price_alert_above?: number | null
          price_alert_below?: number | null
          symbol: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          name?: string | null
          notes?: string | null
          price_alert_above?: number | null
          price_alert_below?: number | null
          symbol?: string
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["app_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      app_role: "admin" | "user" | "premium"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      app_role: ["admin", "user", "premium"],
    },
  },
} as const
