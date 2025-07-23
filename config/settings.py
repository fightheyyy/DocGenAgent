"""
多Agent文档生成系统配置
"""

import logging
from typing import Dict, Any

# 系统配置
SYSTEM_CONFIG = {
    # OpenRouter配置
    'openrouter': {
        'api_key': 'YOUR_OPEN_ROUTER_KEY',
        'base_url': 'https://openrouter.ai/api/v1',
        'model': 'google/gemini-2.5-flash',
        'max_tokens': 10000,
        'temperature': 0.7,
        'timeout': 30
    },
    
    # 日志配置
    'logging': {
        'level': logging.INFO,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_path': None  # 设置为None表示只输出到控制台
    },
    
    # 并发控制配置
    'concurrency': {
        'orchestrator_agent': {
            'max_workers': 5,
            'description': '编排代理 - 按大章节并行生成写作指导'
        },
        'react_agent': {
            'max_workers': 5,
            'description': '检索代理 - 按子章节并行执行ReAct循环'
        },
        'content_generator_agent': {
            'max_workers': 5,
            'description': '内容生成代理 - 按子章节并行生成内容'
        },
        'rate_limiting': {
            'delay_between_requests': 4,  # 秒
            'description': '请求间隔控制，防止API超限'
        }
    },
    
    # 文档生成配置
    'generation': {
        'max_sections': 50,
        'default_section_length': 1000,
        'parallel_generation': False,
        'max_retries': 3
    },
    
    # 质量控制配置
    'quality': {
        'min_quality_score': 0.8,
        'max_improvement_attempts': 3,
        'quality_dimensions': {
            'length': 0.15,
            'completeness': 0.25,
            'coherence': 0.20,
            'accuracy': 0.25,
            'readability': 0.15
        }
    },
    
    # Agent配置
    'agents': {
        'orchestrator': {
            'max_outline_depth': 4,
            'min_sections_per_chapter': 2,
            'max_sections_per_chapter': 10
        },
        'section_writer': {
            'max_query_rounds': 3,
            'max_queries_per_round': 5,
            'context_relevance_threshold': 0.7
        },
        'content_generator': {
            'max_content_length': 5000,
            'min_content_length': 200,
            'quality_check_rounds': 2
        }
    }
}


class ConcurrencyManager:
    """并发管理器 - 统一管理所有Agent的并发设置"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or SYSTEM_CONFIG['concurrency']
        from threading import Lock
        self._locks = {}  # 为每个Agent创建独立的锁
    
    def get_max_workers(self, agent_name: str) -> int:
        """获取指定Agent的最大线程数"""
        agent_config = self.config.get(agent_name, {})
        return agent_config.get('max_workers', 1)
    
    def set_max_workers(self, agent_name: str, max_workers: int):
        """设置指定Agent的最大线程数"""
        if agent_name not in self.config:
            self.config[agent_name] = {}
        self.config[agent_name]['max_workers'] = max_workers
    
    def get_rate_limit_delay(self) -> float:
        """获取请求间隔时间"""
        return self.config.get('rate_limiting', {}).get('delay_between_requests', 4)
    
    def set_rate_limit_delay(self, delay: float):
        """设置请求间隔时间"""
        if 'rate_limiting' not in self.config:
            self.config['rate_limiting'] = {}
        self.config['rate_limiting']['delay_between_requests'] = delay
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有并发设置"""
        return self.config.copy()
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """批量更新并发设置"""
        self.config.update(new_settings)
    
    def get_lock(self, agent_name: str):
        """获取指定Agent的线程锁"""
        from threading import Lock
        if agent_name not in self._locks:
            self._locks[agent_name] = Lock()
        return self._locks[agent_name]
    
    def print_settings(self):
        """打印当前并发设置"""
        print("🔧 当前并发设置:")
        print("=" * 50)
        for agent_name, settings in self.config.items():
            if agent_name == 'rate_limiting':
                delay = settings.get('delay_between_requests', 4)
                print(f"⏱️  请求间隔: {delay}秒")
            elif 'max_workers' in settings:
                max_workers = settings['max_workers']
                description = settings.get('description', '')
                print(f"🧵 {agent_name}: {max_workers} 线程 - {description}")
        print("=" * 50)


def get_config() -> Dict[str, Any]:
    """获取系统配置"""
    return SYSTEM_CONFIG

def get_concurrency_manager() -> ConcurrencyManager:
    """获取并发管理器实例"""
    return ConcurrencyManager()

def setup_logging():
    """设置日志系统"""
    config = SYSTEM_CONFIG['logging']
    
    logging.basicConfig(
        level=config['level'],
        format=config['format'],
        filename=config['file_path'],
        filemode='a' if config['file_path'] else None,
        force=True  # 强制重新配置日志
    )
    
    # 获取根日志记录器并设置立即刷新
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.flush()
        # 设置立即刷新，确保多线程环境下日志及时显示
        if hasattr(handler, 'stream'):
            handler.stream.flush()
    
    # 设置第三方库日志级别
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING) 