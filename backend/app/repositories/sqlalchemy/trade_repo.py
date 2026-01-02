from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.trade_repo import TradeRepository
from app.schemas.trades import TradeStatus, TradeCreateRequest, TradeUpdateRequest
from app.domain.models import Trade, Strategy
from app.domain.errors import NotFoundError, ConflictError


class SQLAlchemyTradeRepository(TradeRepository):
    """SQLAlchemy implementation of trade repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_trade(self, trade_data: TradeCreateRequest) -> int:
        """Create a new trade and return its ID"""
        try:
            # Set fill_price to entry_price if not provided
            fill_price = trade_data.fill_price or trade_data.entry_price
            
            trade = Trade(
                strategy_id=trade_data.strategy_id,
                contract_symbol=trade_data.contract_symbol,
                ticker=trade_data.ticker,
                entry_price=trade_data.entry_price,
                fill_price=fill_price,
                quantity=trade_data.quantity,
                stop_loss=trade_data.stop_loss,
                take_profit=trade_data.take_profit,
                notifications_enabled=trade_data.notifications_enabled,
                notes=trade_data.notes,
                status=TradeStatus.OPEN,
                entry_date=datetime.utcnow()
            )
            
            self.session.add(trade)
            await self.session.flush()
            await self.session.refresh(trade)
            
            return trade.id
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_trade_by_id(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """Get a single trade by ID"""
        try:
            result = await self.session.execute(
                sa.select(
                    Trade,
                    Strategy.name.label('strategy_name')
                )
                .outerjoin(Strategy, Trade.strategy_id == Strategy.id)
                .where(Trade.id == trade_id)
            )
            row = result.first()
            
            if not row:
                return None
            
            trade, strategy_name = row
            
            return {
                'id': trade.id,
                'strategy_id': trade.strategy_id,
                'contract_symbol': trade.contract_symbol,
                'ticker': trade.ticker,
                'entry_date': trade.entry_date,
                'entry_price': trade.entry_price,
                'fill_price': trade.fill_price,
                'quantity': trade.quantity,
                'stop_loss': trade.stop_loss,
                'take_profit': trade.take_profit,
                'status': trade.status,
                'exit_date': trade.exit_date,
                'exit_price': trade.exit_price,
                'pnl': trade.pnl,
                'notifications_enabled': trade.notifications_enabled,
                'notes': trade.notes,
                'strategy_name': strategy_name
            }
            
        except Exception as e:
            raise e
    
    async def get_all_trades(
        self, 
        status: Optional[TradeStatus] = None,
        strategy_id: Optional[int] = None,
        ticker: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all trades with optional filters"""
        try:
            query = (
                sa.select(
                    Trade,
                    Strategy.name.label('strategy_name')
                )
                .outerjoin(Strategy, Trade.strategy_id == Strategy.id)
                .order_by(Trade.entry_date.desc())
            )
            
            # Apply filters
            if status:
                query = query.where(Trade.status == status)
            if strategy_id:
                query = query.where(Trade.strategy_id == strategy_id)
            if ticker:
                query = query.where(Trade.ticker == ticker.upper())
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            rows = result.all()
            
            trades = []
            for row in rows:
                trade, strategy_name = row
                trades.append({
                    'id': trade.id,
                    'strategy_id': trade.strategy_id,
                    'contract_symbol': trade.contract_symbol,
                    'ticker': trade.ticker,
                    'entry_date': trade.entry_date,
                    'entry_price': trade.entry_price,
                    'fill_price': trade.fill_price,
                    'quantity': trade.quantity,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit,
                    'status': trade.status,
                    'exit_date': trade.exit_date,
                    'exit_price': trade.exit_price,
                    'pnl': trade.pnl,
                    'notifications_enabled': trade.notifications_enabled,
                    'notes': trade.notes,
                    'strategy_name': strategy_name
                })
            
            return trades
            
        except Exception as e:
            raise e
    
    async def get_open_trades(self) -> List[Dict[str, Any]]:
        """Get all open trades"""
        return await self.get_all_trades(status=TradeStatus.OPEN)
    
    async def update_trade(self, trade_id: int, updates: TradeUpdateRequest) -> bool:
        """Update a trade"""
        try:
            # Check if trade exists
            trade = await self.session.get(Trade, trade_id)
            if not trade:
                return False
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(trade, field):
                    setattr(trade, field, value)
            
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def close_trade(self, trade_id: int, exit_price: float) -> Optional[Dict[str, Any]]:
        """Close a trade and calculate P&L"""
        try:
            # Get trade
            trade = await self.session.get(Trade, trade_id)
            if not trade:
                return None
            
            if trade.status != TradeStatus.OPEN:
                raise ConflictError("Trade is already closed")
            
            # Calculate P&L
            fill_price = trade.fill_price or trade.entry_price
            quantity = trade.quantity or 1
            
            # P&L = (exit - entry) * quantity * 100 (options multiplier)
            pnl = (exit_price - fill_price) * quantity * 100
            
            # Update trade
            trade.exit_price = exit_price
            trade.exit_date = datetime.utcnow()
            trade.pnl = pnl
            trade.status = TradeStatus.CLOSED_WIN if pnl >= 0 else TradeStatus.CLOSED_LOSS
            
            await self.session.commit()
            
            # Return updated trade data
            return await self.get_trade_by_id(trade_id)
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def delete_trade(self, trade_id: int) -> bool:
        """Delete a trade"""
        try:
            trade = await self.session.get(Trade, trade_id)
            if not trade:
                return False
            
            await self.session.delete(trade)
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_trade_stats(self) -> Dict[str, Any]:
        """Get aggregate trade statistics"""
        try:
            # Total trades
            total_result = await self.session.execute(sa.select(sa.func.count(Trade.id)))
            total = total_result.scalar()
            
            # Open trades
            open_result = await self.session.execute(
                sa.select(sa.func.count(Trade.id))
                .where(Trade.status == TradeStatus.OPEN)
            )
            open_count = open_result.scalar()
            
            # Wins
            wins_result = await self.session.execute(
                sa.select(sa.func.count(Trade.id))
                .where(Trade.status == TradeStatus.CLOSED_WIN)
            )
            wins = wins_result.scalar()
            
            # Losses
            losses_result = await self.session.execute(
                sa.select(sa.func.count(Trade.id))
                .where(Trade.status == TradeStatus.CLOSED_LOSS)
            )
            losses = losses_result.scalar()
            
            # Total P&L
            pnl_result = await self.session.execute(
                sa.select(sa.func.coalesce(sa.func.sum(Trade.pnl), 0))
                .where(Trade.pnl.isnot(None))
            )
            total_pnl = pnl_result.scalar()
            
            # Additional stats
            closed = wins + losses
            win_rate = round((wins / closed * 100), 1) if closed > 0 else 0
            
            # Average win/loss
            avg_win_result = await self.session.execute(
                sa.select(sa.func.avg(Trade.pnl))
                .where(Trade.status == TradeStatus.CLOSED_WIN)
            )
            avg_win = avg_win_result.scalar()
            
            avg_loss_result = await self.session.execute(
                sa.select(sa.func.avg(Trade.pnl))
                .where(Trade.status == TradeStatus.CLOSED_LOSS)
            )
            avg_loss = avg_loss_result.scalar()
            
            # Largest win/loss
            largest_win_result = await self.session.execute(
                sa.select(sa.func.max(Trade.pnl))
                .where(Trade.status == TradeStatus.CLOSED_WIN)
            )
            largest_win = largest_win_result.scalar()
            
            largest_loss_result = await self.session.execute(
                sa.select(sa.func.min(Trade.pnl))
                .where(Trade.status == TradeStatus.CLOSED_LOSS)
            )
            largest_loss = largest_loss_result.scalar()
            
            # Profit factor
            gross_profit_result = await self.session.execute(
                sa.select(sa.func.sum(Trade.pnl))
                .where(Trade.status == TradeStatus.CLOSED_WIN)
            )
            gross_profit = gross_profit_result.scalar() or 0
            
            gross_loss_result = await self.session.execute(
                sa.select(sa.func.sum(Trade.pnl))
                .where(Trade.status == TradeStatus.CLOSED_LOSS)
            )
            gross_loss = abs(gross_loss_result.scalar() or 0)
            
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else None
            
            return {
                "total_trades": total,
                "open_trades": open_count,
                "closed_trades": closed,
                "wins": wins,
                "losses": losses,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "avg_win": round(avg_win, 2) if avg_win else None,
                "avg_loss": round(avg_loss, 2) if avg_loss else None,
                "largest_win": round(largest_win, 2) if largest_win else None,
                "largest_loss": round(largest_loss, 2) if largest_loss else None,
                "profit_factor": round(profit_factor, 2) if profit_factor else None
            }
            
        except Exception as e:
            raise e
    
    async def get_trades_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Get all trades for a specific ticker"""
        return await self.get_all_trades(ticker=ticker)
    
    async def get_trades_by_strategy(self, strategy_id: int) -> List[Dict[str, Any]]:
        """Get all trades for a specific strategy"""
        return await self.get_all_trades(strategy_id=strategy_id)
    
    async def batch_update_trades(self, trade_ids: List[int], updates: Dict[str, Any]) -> int:
        """Update multiple trades at once"""
        try:
            # Build update statement
            stmt = (
                sa.update(Trade)
                .where(Trade.id.in_(trade_ids))
                .values(**updates)
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def batch_delete_trades(self, trade_ids: List[int]) -> int:
        """Delete multiple trades at once"""
        try:
            stmt = sa.delete(Trade).where(Trade.id.in_(trade_ids))
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_trade_performance_analysis(
        self, 
        period: str = "3mo",
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """Get detailed trade performance analysis"""
        try:
            # Calculate date filter based on period
            now = datetime.utcnow()
            if period == "1mo":
                start_date = now - timedelta(days=30)
            elif period == "3mo":
                start_date = now - timedelta(days=90)
            elif period == "6mo":
                start_date = now - timedelta(days=180)
            elif period == "1y":
                start_date = now - timedelta(days=365)
            else:  # all
                start_date = None
            
            # Base query
            query = sa.select(Trade).where(Trade.pnl.isnot(None))
            if start_date:
                query = query.where(Trade.entry_date >= start_date)
            
            result = await self.session.execute(query)
            trades = result.scalars().all()
            
            # Group data
            grouped_data = {}
            for trade in trades:
                if group_by == "month":
                    key = trade.entry_date.strftime("%Y-%m")
                elif group_by == "week":
                    key = trade.entry_date.strftime("%Y-W%U")
                elif group_by == "day":
                    key = trade.entry_date.strftime("%Y-%m-%d")
                elif group_by == "quarter":
                    quarter = (trade.entry_date.month - 1) // 3 + 1
                    key = f"{trade.entry_date.year}-Q{quarter}"
                else:
                    key = trade.entry_date.strftime("%Y-%m")
                
                if key not in grouped_data:
                    grouped_data[key] = {
                        "period": key,
                        "trades": 0,
                        "wins": 0,
                        "losses": 0,
                        "pnl": 0,
                        "win_rate": 0
                    }
                
                grouped_data[key]["trades"] += 1
                grouped_data[key]["pnl"] += trade.pnl or 0
                
                if trade.status == TradeStatus.CLOSED_WIN:
                    grouped_data[key]["wins"] += 1
                elif trade.status == TradeStatus.CLOSED_LOSS:
                    grouped_data[key]["losses"] += 1
            
            # Calculate win rates
            for period_data in grouped_data.values():
                total_closed = period_data["wins"] + period_data["losses"]
                if total_closed > 0:
                    period_data["win_rate"] = round(
                        (period_data["wins"] / total_closed) * 100, 1
                    )
            
            return {
                "period": period,
                "group_by": group_by,
                "data_points": list(grouped_data.values()),
                "summary": {
                    "total_periods": len(grouped_data),
                    "avg_trades_per_period": sum(d["trades"] for d in grouped_data.values()) / len(grouped_data) if grouped_data else 0
                }
            }
            
        except Exception as e:
            raise e
    
    async def search_trades(self, query: str) -> List[Dict[str, Any]]:
        """Search trades by contract symbol or notes"""
        try:
            search_pattern = f"%{query.upper()}%"
            
            result = await self.session.execute(
                sa.select(
                    Trade,
                    Strategy.name.label('strategy_name')
                )
                .outerjoin(Strategy, Trade.strategy_id == Strategy.id)
                .where(
                    sa.or_(
                        Trade.contract_symbol.ilike(search_pattern),
                        Trade.notes.ilike(search_pattern)
                    )
                )
                .order_by(Trade.entry_date.desc())
            )
            
            rows = result.all()
            
            trades = []
            for row in rows:
                trade, strategy_name = row
                trades.append({
                    'id': trade.id,
                    'strategy_id': trade.strategy_id,
                    'contract_symbol': trade.contract_symbol,
                    'ticker': trade.ticker,
                    'entry_date': trade.entry_date,
                    'entry_price': trade.entry_price,
                    'fill_price': trade.fill_price,
                    'quantity': trade.quantity,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit,
                    'status': trade.status,
                    'exit_date': trade.exit_date,
                    'exit_price': trade.exit_price,
                    'pnl': trade.pnl,
                    'notifications_enabled': trade.notifications_enabled,
                    'notes': trade.notes,
                    'strategy_name': strategy_name
                })
            
            return trades
            
        except Exception as e:
            raise e
