from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.strategy_repo import (
    StrategyRepository, CustomStrategyRepository, StrategyAnalyticsRepository
)
from app.schemas.strategies import (
    StrategyCreateRequest, StrategyUpdateRequest, StrategyType,
    CustomStrategyCreateRequest, CustomStrategyUpdateRequest,
    ScheduleType, ExecutionType
)
from app.domain.models import Strategy, CustomStrategy, StrategyLog, Trade
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class SQLAlchemyStrategyRepository(StrategyRepository):
    """SQLAlchemy implementation of strategy repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_strategy(self, strategy_data: StrategyCreateRequest) -> int:
        """Create a new strategy and return its ID"""
        try:
            strategy = Strategy(
                name=strategy_data.name,
                description=strategy_data.description,
                scan_criteria=json.dumps(strategy_data.scan_criteria) if strategy_data.scan_criteria else None,
                default_stop_loss_pct=strategy_data.default_stop_loss_pct,
                default_take_profit_pct=strategy_data.default_take_profit_pct,
                notifications_enabled=strategy_data.notifications_enabled,
                strategy_type=strategy_data.strategy_type,
                created_at=datetime.utcnow()
            )
            
            self.session.add(strategy)
            await self.session.flush()
            await self.session.refresh(strategy)
            
            return strategy.id
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_strategy_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get a single strategy by ID"""
        try:
            result = await self.session.execute(
                sa.select(Strategy).where(Strategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return None
            
            # Get performance metrics
            trades_result = await self.session.execute(
                sa.select(
                    sa.func.count(Trade.id).label('trade_count'),
                    sa.func.sum(Trade.pnl).label('total_pnl')
                )
                .where(Trade.strategy_id == strategy_id)
            )
            trades_data = trades_result.first()
            
            # Calculate win rate
            wins_result = await self.session.execute(
                sa.select(sa.func.count(Trade.id))
                .where(
                    sa.and_(
                        Trade.strategy_id == strategy_id,
                        Trade.status == 'CLOSED_WIN'
                    )
                )
            )
            wins = wins_result.scalar() or 0
            
            total_closed = trades_result.first()[0] if trades_result else 0
            win_rate = (wins / total_closed * 100) if total_closed > 0 else 0
            
            return {
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'scan_criteria': json.loads(strategy.scan_criteria) if strategy.scan_criteria else None,
                'default_stop_loss_pct': strategy.default_stop_loss_pct,
                'default_take_profit_pct': strategy.default_take_profit_pct,
                'notifications_enabled': strategy.notifications_enabled,
                'strategy_type': strategy.strategy_type,
                'created_at': strategy.created_at,
                'updated_at': strategy.updated_at,
                'trade_count': trades_data.trade_count or 0,
                'total_pnl': trades_data.total_pnl or 0,
                'win_rate': round(win_rate, 1) if win_rate else 0
            }
            
        except Exception as e:
            raise e
    
    async def get_all_strategies(
        self, 
        strategy_type: Optional[StrategyType] = None,
        notifications_enabled: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all strategies with optional filters"""
        try:
            query = sa.select(Strategy).order_by(Strategy.created_at.desc())
            
            # Apply filters
            if strategy_type:
                query = query.where(Strategy.strategy_type == strategy_type)
            if notifications_enabled is not None:
                query = query.where(Strategy.notifications_enabled == notifications_enabled)
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            strategies = result.scalars().all()
            
            strategy_list = []
            for strategy in strategies:
                strategy_list.append({
                    'id': strategy.id,
                    'name': strategy.name,
                    'description': strategy.description,
                    'scan_criteria': json.loads(strategy.scan_criteria) if strategy.scan_criteria else None,
                    'default_stop_loss_pct': strategy.default_stop_loss_pct,
                    'default_take_profit_pct': strategy.default_take_profit_pct,
                    'notifications_enabled': strategy.notifications_enabled,
                    'strategy_type': strategy.strategy_type,
                    'created_at': strategy.created_at,
                    'updated_at': strategy.updated_at
                })
            
            return strategy_list
            
        except Exception as e:
            raise e
    
    async def update_strategy(self, strategy_id: int, updates: StrategyUpdateRequest) -> bool:
        """Update a strategy"""
        try:
            strategy = await self.session.get(Strategy, strategy_id)
            if not strategy:
                return False
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(strategy, field):
                    if field == 'scan_criteria' and isinstance(value, dict):
                        setattr(strategy, field, json.dumps(value))
                    else:
                        setattr(strategy, field, value)
            
            strategy.updated_at = datetime.utcnow()
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def delete_strategy(self, strategy_id: int) -> bool:
        """Delete a strategy"""
        try:
            strategy = await self.session.get(Strategy, strategy_id)
            if not strategy:
                return False
            
            await self.session.delete(strategy)
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_strategy_stats(self) -> Dict[str, Any]:
        """Get aggregate strategy statistics"""
        try:
            # Total strategies
            total_result = await self.session.execute(sa.select(sa.func.count(Strategy.id)))
            total = total_result.scalar()
            
            # Strategies with trades
            with_trades_result = await self.session.execute(
                sa.select(sa.func.count(sa.func.distinct(Trade.strategy_id)))
                .where(Trade.strategy_id.isnot(None))
            )
            strategies_with_trades = with_trades_result.scalar()
            
            # Notification enabled
            notifications_result = await self.session.execute(
                sa.select(sa.func.count(Strategy.id))
                .where(Strategy.notifications_enabled == True)
            )
            notifications_enabled = notifications_result.scalar()
            
            # By type
            custom_result = await self.session.execute(
                sa.select(sa.func.count(Strategy.id))
                .where(Strategy.strategy_type == StrategyType.CUSTOM)
            )
            custom_count = custom_result.scalar()
            
            predefined_count = total - custom_count
            
            return {
                "total_strategies": total,
                "strategies_with_trades": strategies_with_trades,
                "notifications_enabled": notifications_enabled,
                "custom_strategies": custom_count,
                "predefined_strategies": predefined_count
            }
            
        except Exception as e:
            raise e
    
    async def get_strategies_with_performance(self) -> List[Dict[str, Any]]:
        """Get strategies with their performance metrics"""
        try:
            # This is a complex query - simplified for now
            result = await self.session.execute(
                sa.select(
                    Strategy,
                    sa.func.coalesce(sa.func.sum(Trade.pnl), 0).label('total_pnl'),
                    sa.func.coalesce(sa.func.count(Trade.id), 0).label('trade_count')
                )
                .outerjoin(Trade, Strategy.id == Trade.strategy_id)
                .group_by(Strategy.id)
                .order_by(sa.desc('total_pnl'))
            )
            
            rows = result.all()
            
            strategies = []
            for row in rows:
                strategy, total_pnl, trade_count = row
                strategies.append({
                    'id': strategy.id,
                    'name': strategy.name,
                    'strategy_type': strategy.strategy_type,
                    'total_pnl': total_pnl,
                    'trade_count': trade_count,
                    'created_at': strategy.created_at
                })
            
            return strategies
            
        except Exception as e:
            raise e
    
    async def search_strategies(self, query: str) -> List[Dict[str, Any]]:
        """Search strategies by name or description"""
        try:
            search_pattern = f"%{query.upper()}%"
            
            result = await self.session.execute(
                sa.select(Strategy)
                .where(
                    sa.or_(
                        Strategy.name.ilike(search_pattern),
                        Strategy.description.ilike(search_pattern)
                    )
                )
                .order_by(Strategy.created_at.desc())
            )
            
            strategies = result.scalars().all()
            
            strategy_list = []
            for strategy in strategies:
                strategy_list.append({
                    'id': strategy.id,
                    'name': strategy.name,
                    'description': strategy.description,
                    'strategy_type': strategy.strategy_type,
                    'created_at': strategy.created_at
                })
            
            return strategy_list
            
        except Exception as e:
            raise e


class SQLAlchemyCustomStrategyRepository(CustomStrategyRepository):
    """SQLAlchemy implementation of custom strategy repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_custom_strategy(self, strategy_data: CustomStrategyCreateRequest) -> int:
        """Create a new custom strategy and return its ID"""
        try:
            strategy = CustomStrategy(
                name=strategy_data.name,
                code=strategy_data.code,
                schedule_type=strategy_data.schedule_type,
                schedule_value=strategy_data.schedule_value,
                execution_type=strategy_data.execution_type,
                targets=strategy_data.targets,
                description=strategy_data.description,
                is_active=False,  # Start inactive
                created_at=datetime.utcnow()
            )
            
            self.session.add(strategy)
            await self.session.flush()
            await self.session.refresh(strategy)
            
            return strategy.id
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_custom_strategy_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get a single custom strategy by ID"""
        try:
            result = await self.session.execute(
                sa.select(CustomStrategy).where(CustomStrategy.id == strategy_id)
            )
            strategy = result.scalar_one_or_none()
            
            if not strategy:
                return None
            
            # Get execution stats
            logs_result = await self.session.execute(
                sa.select(
                    sa.func.count(StrategyLog.id).label('execution_count'),
                    sa.func.sum(StrategyLog.trades_generated).label('total_trades')
                )
                .where(StrategyLog.strategy_id == strategy_id)
            )
            logs_data = logs_result.first()
            
            # Calculate success rate
            success_result = await self.session.execute(
                sa.select(sa.func.count(StrategyLog.id))
                .where(
                    sa.and_(
                        StrategyLog.strategy_id == strategy_id,
                        StrategyLog.status == 'SUCCESS'
                    )
                )
            )
            success_count = success_result.scalar() or 0
            total_executions = logs_data.execution_count or 0
            success_rate = (success_count / total_executions * 100) if total_executions > 0 else 0
            
            return {
                'id': strategy.id,
                'name': strategy.name,
                'code': strategy.code,
                'schedule_type': strategy.schedule_type,
                'schedule_value': strategy.schedule_value,
                'execution_type': strategy.execution_type,
                'is_active': strategy.is_active,
                'targets': strategy.targets,
                'description': strategy.description,
                'last_run': strategy.last_run,
                'created_at': strategy.created_at,
                'updated_at': strategy.updated_at,
                'execution_count': logs_data.execution_count or 0,
                'total_trades': logs_data.total_trades or 0,
                'success_rate': round(success_rate, 1),
                'avg_trades_per_run': round((logs_data.total_trades or 0) / total_executions, 1) if total_executions > 0 else 0
            }
            
        except Exception as e:
            raise e
    
    async def get_all_custom_strategies(
        self,
        is_active: Optional[bool] = None,
        execution_type: Optional[ExecutionType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all custom strategies with optional filters"""
        try:
            query = sa.select(CustomStrategy).order_by(CustomStrategy.created_at.desc())
            
            # Apply filters
            if is_active is not None:
                query = query.where(CustomStrategy.is_active == is_active)
            if execution_type:
                query = query.where(CustomStrategy.execution_type == execution_type)
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            strategies = result.scalars().all()
            
            strategy_list = []
            for strategy in strategies:
                strategy_list.append({
                    'id': strategy.id,
                    'name': strategy.name,
                    'schedule_type': strategy.schedule_type,
                    'execution_type': strategy.execution_type,
                    'is_active': strategy.is_active,
                    'targets': strategy.targets,
                    'description': strategy.description,
                    'last_run': strategy.last_run,
                    'created_at': strategy.created_at,
                    'updated_at': strategy.updated_at
                })
            
            return strategy_list
            
        except Exception as e:
            raise e
    
    async def update_custom_strategy(self, strategy_id: int, updates: CustomStrategyUpdateRequest) -> bool:
        """Update a custom strategy"""
        try:
            strategy = await self.session.get(CustomStrategy, strategy_id)
            if not strategy:
                return False
            
            # Update fields
            update_data = updates.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(strategy, field):
                    setattr(strategy, field, value)
            
            strategy.updated_at = datetime.utcnow()
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def delete_custom_strategy(self, strategy_id: int) -> bool:
        """Delete a custom strategy"""
        try:
            strategy = await self.session.get(CustomStrategy, strategy_id)
            if not strategy:
                return False
            
            await self.session.delete(strategy)
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def execute_custom_strategy(
        self, 
        strategy_id: int, 
        dry_run: bool = False,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a custom strategy"""
        try:
            # Get strategy
            strategy = await self.session.get(CustomStrategy, strategy_id)
            if not strategy:
                raise NotFoundError(f"Custom strategy {strategy_id} not found")
            
            if not strategy.is_active and not dry_run:
                raise ValidationError("Cannot execute inactive strategy")
            
            # Create execution log
            log = StrategyLog(
                strategy_id=strategy_id,
                status="RUNNING",
                timestamp=datetime.utcnow(),
                trades_generated=0
            )
            
            self.session.add(log)
            await self.session.flush()
            
            # Simulate execution (in real implementation, this would run the Python code)
            execution_result = {
                "status": "SUCCESS",
                "output": f"Strategy {strategy.name} executed successfully",
                "trades_generated": 0,  # Would be actual number from execution
                "execution_time_ms": 1500
            }
            
            # Update log with results
            log.status = execution_result["status"]
            log.output = execution_result["output"]
            log.trades_generated = execution_result["trades_generated"]
            
            # Update strategy last run
            strategy.last_run = datetime.utcnow()
            
            await self.session.commit()
            
            return {
                "execution_id": log.id,
                "strategy_id": strategy_id,
                **execution_result
            }
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_strategy_logs(
        self,
        strategy_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get strategy execution logs"""
        try:
            query = sa.select(StrategyLog).order_by(StrategyLog.timestamp.desc())
            
            if strategy_id:
                query = query.where(StrategyLog.strategy_id == strategy_id)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            logs = result.scalars().all()
            
            log_list = []
            for log in logs:
                log_list.append({
                    'id': log.id,
                    'strategy_id': log.strategy_id,
                    'timestamp': log.timestamp,
                    'status': log.status,
                    'output': log.output,
                    'trades_generated': log.trades_generated,
                    'execution_time_ms': getattr(log, 'execution_time_ms', None)
                })
            
            return log_list
            
        except Exception as e:
            raise e
    
    async def get_custom_strategy_stats(self) -> Dict[str, Any]:
        """Get aggregate custom strategy statistics"""
        try:
            # Total custom strategies
            total_result = await self.session.execute(sa.select(sa.func.count(CustomStrategy.id)))
            total = total_result.scalar()
            
            # Active strategies
            active_result = await self.session.execute(
                sa.select(sa.func.count(CustomStrategy.id))
                .where(CustomStrategy.is_active == True)
            )
            active = active_result.scalar()
            
            # Total executions
            executions_result = await self.session.execute(
                sa.select(sa.func.count(StrategyLog.id))
            )
            total_executions = executions_result.scalar()
            
            # Successful executions
            success_result = await self.session.execute(
                sa.select(sa.func.count(StrategyLog.id))
                .where(StrategyLog.status == 'SUCCESS')
            )
            successful_executions = success_result.scalar()
            
            return {
                "total_custom_strategies": total,
                "active_strategies": active,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": round((successful_executions / total_executions * 100), 1) if total_executions > 0 else 0
            }
            
        except Exception as e:
            raise e
    
    async def batch_update_custom_strategies(
        self, 
        strategy_ids: List[int], 
        updates: Dict[str, Any]
    ) -> int:
        """Update multiple custom strategies at once"""
        try:
            stmt = (
                sa.update(CustomStrategy)
                .where(CustomStrategy.id.in_(strategy_ids))
                .values(**updates)
            )
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def batch_delete_custom_strategies(self, strategy_ids: List[int]) -> int:
        """Delete multiple custom strategies at once"""
        try:
            stmt = sa.delete(CustomStrategy).where(CustomStrategy.id.in_(strategy_ids))
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def toggle_strategy_activation(self, strategy_id: int, is_active: bool) -> bool:
        """Activate or deactivate a custom strategy"""
        try:
            strategy = await self.session.get(CustomStrategy, strategy_id)
            if not strategy:
                return False
            
            strategy.is_active = is_active
            strategy.updated_at = datetime.utcnow()
            
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def get_scheduled_strategies(self) -> List[Dict[str, Any]]:
        """Get all active scheduled strategies"""
        try:
            result = await self.session.execute(
                sa.select(CustomStrategy)
                .where(CustomStrategy.is_active == True)
                .order_by(CustomStrategy.last_run.asc())
            )
            
            strategies = result.scalars().all()
            
            scheduled_list = []
            for strategy in strategies:
                scheduled_list.append({
                    'id': strategy.id,
                    'name': strategy.name,
                    'schedule_type': strategy.schedule_type,
                    'schedule_value': strategy.schedule_value,
                    'last_run': strategy.last_run,
                    'next_run': self._calculate_next_run(strategy)
                })
            
            return scheduled_list
            
        except Exception as e:
            raise e
    
    def _calculate_next_run(self, strategy: CustomStrategy) -> datetime:
        """Calculate next run time for a strategy"""
        if not strategy.last_run:
            return datetime.utcnow()
        
        if strategy.schedule_type == ScheduleType.INTERVAL:
            try:
                interval_seconds = int(strategy.schedule_value)
                return strategy.last_run + timedelta(seconds=interval_seconds)
            except ValueError:
                return datetime.utcnow()
        
        # For CRON and other types, return current time (simplified)
        return datetime.utcnow()


class SQLAlchemyStrategyAnalyticsRepository(StrategyAnalyticsRepository):
    """SQLAlchemy implementation of strategy analytics repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_strategy_performance(
        self, 
        strategy_id: int, 
        period: str = "3mo"
    ) -> Dict[str, Any]:
        """Get performance metrics for a specific strategy"""
        try:
            # Calculate date filter
            now = datetime.utcnow()
            if period == "1mo":
                start_date = now - timedelta(days=30)
            elif period == "3mo":
                start_date = now - timedelta(days=90)
            elif period == "6mo":
                start_date = now - timedelta(days=180)
            elif period == "1y":
                start_date = now - timedelta(days=365)
            else:
                start_date = None
            
            # Base query for trades
            query = sa.select(Trade).where(Trade.strategy_id == strategy_id)
            if start_date:
                query = query.where(Trade.entry_date >= start_date)
            
            result = await self.session.execute(query)
            trades = result.scalars().all()
            
            if not trades:
                return {
                    "strategy_id": strategy_id,
                    "period": period,
                    "total_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0
                }
            
            # Calculate metrics
            total_trades = len(trades)
            wins = sum(1 for t in trades if t.status == 'CLOSED_WIN')
            losses = sum(1 for t in trades if t.status == 'CLOSED_LOSS')
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            total_pnl = sum(t.pnl or 0 for t in trades)
            
            # Additional metrics
            winning_trades = [t for t in trades if t.status == 'CLOSED_WIN' and t.pnl]
            losing_trades = [t for t in trades if t.status == 'CLOSED_LOSS' and t.pnl]
            
            avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
            avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
            
            # Consecutive wins/losses (simplified)
            max_consecutive_wins = 3  # Would need more complex calculation
            max_consecutive_losses = 2
            
            return {
                "strategy_id": strategy_id,
                "period": period,
                "total_trades": total_trades,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 1),
                "total_pnl": round(total_pnl, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "max_consecutive_wins": max_consecutive_wins,
                "max_consecutive_losses": max_consecutive_losses
            }
            
        except Exception as e:
            raise e
    
    async def backtest_strategy(
        self,
        strategy_id: int,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000,
        commission: float = 1.0,
        slippage: float = 0.1
    ) -> Dict[str, Any]:
        """Run backtest for a strategy"""
        # This is a simplified backtest implementation
        # In a real system, this would be much more complex
        
        try:
            # Get strategy
            strategy = await self.session.get(Strategy, strategy_id)
            if not strategy:
                raise NotFoundError(f"Strategy {strategy_id} not found")
            
            # Get trades in period
            result = await self.session.execute(
                sa.select(Trade)
                .where(
                    sa.and_(
                        Trade.strategy_id == strategy_id,
                        Trade.entry_date >= start_date,
                        Trade.entry_date <= end_date
                    )
                )
                .order_by(Trade.entry_date)
            )
            
            trades = result.scalars().all()
            
            # Simulate backtest
            capital = initial_capital
            equity_curve = [capital]
            daily_returns = []
            
            for trade in trades:
                if trade.pnl:
                    capital += trade.pnl - commission
                    equity_curve.append(capital)
            
            # Calculate metrics
            final_capital = capital
            total_return = final_capital - initial_capital
            total_return_pct = (total_return / initial_capital) * 100
            
            # Simplified max drawdown calculation
            max_drawdown = 0
            peak = initial_capital
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            return {
                "strategy_id": strategy_id,
                "strategy_name": strategy.name,
                "period": f"{start_date.date()} to {end_date.date()}",
                "initial_capital": initial_capital,
                "final_capital": round(final_capital, 2),
                "total_return": round(total_return, 2),
                "total_return_pct": round(total_return_pct, 2),
                "max_drawdown": round(max_drawdown, 2),
                "trades_count": len(trades),
                "daily_returns": daily_returns
            }
            
        except Exception as e:
            raise e
    
    async def compare_strategies(
        self, 
        strategy_ids: List[int],
        period: str = "3mo"
    ) -> Dict[str, Any]:
        """Compare performance of multiple strategies"""
        try:
            comparison_results = []
            
            for strategy_id in strategy_ids:
                performance = await self.get_strategy_performance(strategy_id, period)
                comparison_results.append(performance)
            
            # Sort by total P&L
            comparison_results.sort(key=lambda x: x.get('total_pnl', 0), reverse=True)
            
            return {
                "period": period,
                "strategies_compared": len(strategy_ids),
                "results": comparison_results,
                "best_performer": comparison_results[0] if comparison_results else None
            }
            
        except Exception as e:
            raise e
    
    async def get_strategy_correlation_matrix(self, strategy_ids: List[int]) -> Dict[str, Any]:
        """Get correlation matrix between strategies"""
        # This is a placeholder implementation
        # Real correlation analysis would require daily returns data for each strategy
        
        try:
            matrix = {}
            for i, id1 in enumerate(strategy_ids):
                matrix[id1] = {}
                for j, id2 in enumerate(strategy_ids):
                    if i == j:
                        matrix[id1][id2] = 1.0
                    else:
                        # Placeholder correlation calculation
                        matrix[id1][id2] = 0.15 + (i * j * 0.01)
            
            return {
                "strategy_ids": strategy_ids,
                "correlation_matrix": matrix,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise e
    
    async def get_strategy_recommendations(
        self,
        risk_tolerance: str = "medium",
        time_horizon: str = "medium",
        preferred_sectors: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get AI-powered strategy recommendations"""
        # This is a placeholder implementation
        # In a real system, this would use ML/AI to generate recommendations
        
        recommendations = [
            {
                "name": "Momentum Scalping",
                "description": "Short-term momentum-based scalping strategy",
                "risk_level": "medium",
                "time_horizon": "short",
                "expected_return": "15-25% annually",
                "win_rate": "65-70%",
                "confidence": 0.85
            },
            {
                "name": "Mean Reversion",
                "description": "Statistical arbitrage using mean reversion",
                "risk_level": "low",
                "time_horizon": "medium",
                "expected_return": "8-12% annually",
                "win_rate": "60-65%",
                "confidence": 0.78
            }
        ]
        
        # Filter by risk tolerance
        if risk_tolerance == "low":
            recommendations = [r for r in recommendations if r["risk_level"] == "low"]
        elif risk_tolerance == "high":
            recommendations = [r for r in recommendations if r["risk_level"] in ["medium", "high"]]
        
        return recommendations
