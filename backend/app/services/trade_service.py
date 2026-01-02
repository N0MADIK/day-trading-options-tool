from typing import List, Dict, Any, Optional
from datetime import datetime

from app.repositories.trade_repo import TradeRepository
from app.schemas.trades import (
    TradeCreateRequest, TradeUpdateRequest, TradeCloseRequest,
    TradeListRequest, TradeStatsResponse, TradePerformanceResponse,
    TradeBatchRequest, TradeBatchUpdateRequest, TradeAnalysisRequest,
    TradeAnalysisResponse
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class TradeService:
    """Service for trade management operations"""
    
    def __init__(self, trade_repository: TradeRepository):
        self.trade_repo = trade_repository
    
    async def create_trade(self, trade_data: TradeCreateRequest) -> Dict[str, Any]:
        """Create a new trade"""
        try:
            # Validate trade data
            if trade_data.stop_loss and trade_data.take_profit:
                if trade_data.stop_loss >= trade_data.take_profit:
                    raise ValidationError("Stop loss must be less than take profit")
            
            # Create trade
            trade_id = await self.trade_repo.create_trade(trade_data)
            
            # Return created trade
            created_trade = await self.trade_repo.get_trade_by_id(trade_id)
            
            return {
                "success": True,
                "trade_id": trade_id,
                "trade": created_trade
            }
            
        except Exception as e:
            raise e
    
    async def get_trade_by_id(self, trade_id: int) -> Dict[str, Any]:
        """Get a single trade by ID"""
        trade = await self.trade_repo.get_trade_by_id(trade_id)
        
        if not trade:
            raise NotFoundError(f"Trade with ID {trade_id} not found")
        
        return trade
    
    async def list_trades(self, request: TradeListRequest) -> List[Dict[str, Any]]:
        """List trades with optional filters"""
        try:
            trades = await self.trade_repo.get_all_trades(
                status=request.status,
                strategy_id=request.strategy_id,
                ticker=request.ticker,
                limit=request.limit,
                offset=request.offset
            )
            
            return trades
            
        except Exception as e:
            raise e
    
    async def get_open_trades(self) -> List[Dict[str, Any]]:
        """Get all open trades"""
        try:
            return await self.trade_repo.get_open_trades()
        except Exception as e:
            raise e
    
    async def update_trade(self, trade_id: int, updates: TradeUpdateRequest) -> Dict[str, Any]:
        """Update a trade"""
        try:
            # Check if trade exists
            existing_trade = await self.trade_repo.get_trade_by_id(trade_id)
            if not existing_trade:
                raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            # Validate updates
            if updates.stop_loss and updates.take_profit:
                if updates.stop_loss >= updates.take_profit:
                    raise ValidationError("Stop loss must be less than take profit")
            
            # Update trade
            success = await self.trade_repo.update_trade(trade_id, updates)
            
            if not success:
                raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            # Return updated trade
            updated_trade = await self.trade_repo.get_trade_by_id(trade_id)
            
            return {
                "success": True,
                "trade": updated_trade
            }
            
        except Exception as e:
            raise e
    
    async def close_trade(self, trade_id: int, request: TradeCloseRequest) -> Dict[str, Any]:
        """Close a trade and calculate P&L"""
        try:
            # Check if trade exists and is open
            existing_trade = await self.trade_repo.get_trade_by_id(trade_id)
            if not existing_trade:
                raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            if existing_trade["status"] != "OPEN":
                raise ConflictError("Trade is already closed")
            
            # Close trade
            closed_trade = await self.trade_repo.close_trade(trade_id, request.exit_price)
            
            if not closed_trade:
                raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            return {
                "success": True,
                "trade": closed_trade,
                "pnl": closed_trade["pnl"],
                "status": closed_trade["status"]
            }
            
        except Exception as e:
            raise e
    
    async def delete_trade(self, trade_id: int) -> Dict[str, Any]:
        """Delete a trade"""
        try:
            # Check if trade exists
            existing_trade = await self.trade_repo.get_trade_by_id(trade_id)
            if not existing_trade:
                raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            # Don't allow deletion of open trades (should be closed first)
            if existing_trade["status"] == "OPEN":
                raise ValidationError("Cannot delete open trades. Close them first.")
            
            # Delete trade
            success = await self.trade_repo.delete_trade(trade_id)
            
            if not success:
                raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            return {
                "success": True,
                "message": f"Trade {trade_id} deleted successfully"
            }
            
        except Exception as e:
            raise e
    
    async def get_trade_statistics(self) -> TradeStatsResponse:
        """Get comprehensive trade statistics"""
        try:
            stats = await self.trade_repo.get_trade_stats()
            
            return TradeStatsResponse(**stats)
            
        except Exception as e:
            raise e
    
    async def get_trades_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Get all trades for a specific ticker"""
        try:
            return await self.trade_repo.get_trades_by_ticker(ticker)
        except Exception as e:
            raise e
    
    async def get_trades_by_strategy(self, strategy_id: int) -> List[Dict[str, Any]]:
        """Get all trades for a specific strategy"""
        try:
            return await self.trade_repo.get_trades_by_strategy(strategy_id)
        except Exception as e:
            raise e
    
    async def batch_update_trades(self, request: TradeBatchUpdateRequest) -> Dict[str, Any]:
        """Update multiple trades at once"""
        try:
            # Validate trade IDs exist
            for trade_id in request.trade_ids:
                existing_trade = await self.trade_repo.get_trade_by_id(trade_id)
                if not existing_trade:
                    raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            # Validate updates
            updates = request.updates.dict(exclude_unset=True)
            if updates.get("stop_loss") and updates.get("take_profit"):
                if updates["stop_loss"] >= updates["take_profit"]:
                    raise ValidationError("Stop loss must be less than take profit")
            
            # Batch update
            updated_count = await self.trade_repo.batch_update_trades(
                request.trade_ids, updates
            )
            
            return {
                "success": True,
                "updated_count": updated_count,
                "message": f"Updated {updated_count} trades"
            }
            
        except Exception as e:
            raise e
    
    async def batch_close_trades(self, trade_ids: List[int], exit_prices: List[float]) -> Dict[str, Any]:
        """Close multiple trades at once"""
        try:
            if len(trade_ids) != len(exit_prices):
                raise ValidationError("Trade IDs and exit prices must have same length")
            
            results = []
            for trade_id, exit_price in zip(trade_ids, exit_prices):
                try:
                    result = await self.trade_repo.close_trade(trade_id, exit_price)
                    results.append({
                        "trade_id": trade_id,
                        "success": True,
                        "trade": result
                    })
                except Exception as e:
                    results.append({
                        "trade_id": trade_id,
                        "success": False,
                        "error": str(e)
                    })
            
            successful_count = sum(1 for r in results if r["success"])
            
            return {
                "success": True,
                "total_count": len(trade_ids),
                "successful_count": successful_count,
                "failed_count": len(trade_ids) - successful_count,
                "results": results
            }
            
        except Exception as e:
            raise e
    
    async def batch_delete_trades(self, request: TradeBatchRequest) -> Dict[str, Any]:
        """Delete multiple trades at once"""
        try:
            # Validate trade IDs exist and are not open
            for trade_id in request.trade_ids:
                existing_trade = await self.trade_repo.get_trade_by_id(trade_id)
                if not existing_trade:
                    raise NotFoundError(f"Trade with ID {trade_id} not found")
                
                if existing_trade["status"] == "OPEN":
                    raise ValidationError(f"Cannot delete open trade {trade_id}. Close it first.")
            
            # Batch delete
            deleted_count = await self.trade_repo.batch_delete_trades(request.trade_ids)
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} trades"
            }
            
        except Exception as e:
            raise e
    
    async def get_trade_performance_analysis(self, request: TradeAnalysisRequest) -> TradeAnalysisResponse:
        """Get detailed trade performance analysis"""
        try:
            analysis = await self.trade_repo.get_trade_performance_analysis(
                period=request.period,
                group_by=request.group_by
            )
            
            return TradeAnalysisResponse(**analysis)
            
        except Exception as e:
            raise e
    
    async def search_trades(self, query: str) -> List[Dict[str, Any]]:
        """Search trades by contract symbol or notes"""
        try:
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")
            
            return await self.trade_repo.search_trades(query.strip())
            
        except Exception as e:
            raise e
    
    async def get_trade_performance_details(self, trade_id: int) -> TradePerformanceResponse:
        """Get detailed performance metrics for a specific trade"""
        try:
            trade = await self.trade_repo.get_trade_by_id(trade_id)
            if not trade:
                raise NotFoundError(f"Trade with ID {trade_id} not found")
            
            # Calculate performance metrics
            entry_price = trade["fill_price"] or trade["entry_price"]
            exit_price = trade.get("exit_price")
            quantity = trade["quantity"]
            
            pnl = trade.get("pnl")
            pnl_percent = None
            days_held = None
            
            if exit_price and pnl is not None:
                pnl_percent = (pnl / (entry_price * quantity * 100)) * 100
                
                # Calculate days held
                if trade["exit_date"]:
                    days_held = (trade["exit_date"] - trade["entry_date"]).days
            
            return TradePerformanceResponse(
                trade_id=trade_id,
                contract_symbol=trade["contract_symbol"],
                ticker=trade["ticker"],
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=quantity,
                pnl=pnl,
                pnl_percent=round(pnl_percent, 2) if pnl_percent else None,
                days_held=days_held,
                status=trade["status"],
                strategy_name=trade.get("strategy_name")
            )
            
        except Exception as e:
            raise e
    
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk metrics for open trades"""
        try:
            open_trades = await self.trade_repo.get_open_trades()
            
            total_risk = 0
            trades_at_risk = 0
            trades_in_profit = 0
            
            for trade in open_trades:
                entry_price = trade["fill_price"] or trade["entry_price"]
                stop_loss = trade.get("stop_loss")
                
                if stop_loss:
                    # Calculate potential loss
                    quantity = trade["quantity"]
                    potential_loss = (entry_price - stop_loss) * quantity * 100
                    total_risk += potential_loss
                    trades_at_risk += 1
            
            # Get current market prices (this would need external API call)
            # For now, use entry price as current price
            for trade in open_trades:
                entry_price = trade["fill_price"] or trade["entry_price"]
                # In real implementation, get current price from options API
                # current_price = await get_current_option_price(trade["contract_symbol"])
                current_price = entry_price  # Placeholder
                
                if current_price > entry_price:
                    trades_in_profit += 1
            
            return {
                "open_positions": len(open_trades),
                "trades_at_risk": trades_at_risk,
                "trades_in_profit": trades_in_profit,
                "total_risk_exposure": round(total_risk, 2),
                "avg_risk_per_trade": round(total_risk / trades_at_risk, 2) if trades_at_risk > 0 else 0,
                "risk_percentage": round((trades_at_risk / len(open_trades)) * 100, 1) if open_trades else 0
            }
            
        except Exception as e:
            raise e
