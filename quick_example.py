#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速示例脚本

演示如何使用Gauz文档Agent系统生成长文档
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def example_1():
    """示例1：文物影响评估报告"""
    
    print("=" * 60)
    print("📋 示例1：文物影响评估报告")
    print("=" * 60)
    
    user_query = """
我需要为"白云区鹤边一社吉祥街二巷1号社文体活动中心项目"编写一份文物影响评估报告。

项目情况：
- 原址为一栋两层砖混结构的知青楼，建于1980年代，目前已有安全隐患
- 计划拆除重建为新的社文体活动中心，建筑面积473.6平方米，高度8.8米
- 项目距离白云区登记保护文物单位"医灵古庙"仅6米
- 医灵古庙始建于清雍正二十年（1724年），为三路三开间二进式建筑
- 需要评估新建项目对文物的各种影响，包括风貌、视线、结构安全等

这份报告将提交给文物管理部门审批，需要专业、严谨、符合法规要求。
    """
    
    print(f"📝 用户需求：")
    print(user_query.strip())
    print("\n🚀 开始生成...")
    
    try:
        from main import DocumentGenerationPipeline
        
        pipeline = DocumentGenerationPipeline()
        result_files = pipeline.generate_document(
            user_query.strip(),
            output_dir="examples/heritage_assessment"
        )
        
        print(f"\n✅ 文档生成完成！")
        print(f"📁 输出目录：{result_files['output_directory']}")
        print(f"📄 最终文档：{result_files['final_document']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False

def example_2():
    """示例2：环境影响评估报告"""
    
    print("\n" + "=" * 60)
    print("📋 示例2：环境影响评估报告")
    print("=" * 60)
    
    user_query = """
编写城市中心30层综合办公楼建设项目的环境影响评估报告。

项目概况：
- 总建筑面积：150,000平方米
- 建筑高度：150米，共30层
- 项目用地：商业用地，位于城市核心区
- 周边环境：商业区、居住区、学校等混合区域

评估内容：
- 交通影响分析（车流量、停车需求）
- 噪音污染评估（施工期、运营期）
- 空气质量影响（扬尘、尾气排放）
- 水土保持方案
- 生态环境保护措施
- 社会环境影响评估

该报告需要符合环境影响评价法规要求，为项目环评审批提供依据。
    """
    
    print(f"📝 用户需求：")
    print(user_query.strip())
    print("\n🚀 开始生成...")
    
    try:
        from main import DocumentGenerationPipeline
        
        pipeline = DocumentGenerationPipeline()
        result_files = pipeline.generate_document(
            user_query.strip(),
            output_dir="examples/environmental_assessment"
        )
        
        print(f"\n✅ 文档生成完成！")
        print(f"📁 输出目录：{result_files['output_directory']}")
        print(f"📄 最终文档：{result_files['final_document']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False

def example_3():
    """示例3：技术方案书"""
    
    print("\n" + "=" * 60)
    print("📋 示例3：技术方案书")
    print("=" * 60)
    
    user_query = """
为智慧城市数字化转型项目编写技术实施方案书。

项目目标：
构建涵盖政务服务、城市治理、民生服务的综合性智慧城市平台

技术架构：
- 基础设施层：云计算、大数据、物联网、5G网络
- 数据层：城市数据湖、数据治理、数据安全
- 应用层：政务应用、城管应用、民生应用
- 展示层：统一门户、移动APP、大屏展示

实施内容：
- 系统总体架构设计
- 各子系统详细设计
- 数据集成与共享方案
- 网络安全保障体系
- 项目实施计划和里程碑
- 风险评估与应对措施
- 运维保障方案

方案需要技术先进、架构合理、实施可行，为项目招投标提供详细的技术依据。
    """
    
    print(f"📝 用户需求：")
    print(user_query.strip())
    print("\n🚀 开始生成...")
    
    try:
        from main import DocumentGenerationPipeline
        
        pipeline = DocumentGenerationPipeline()
        result_files = pipeline.generate_document(
            user_query.strip(),
            output_dir="examples/technical_solution"
        )
        
        print(f"\n✅ 文档生成完成！")
        print(f"📁 输出目录：{result_files['output_directory']}")
        print(f"📄 最终文档：{result_files['final_document']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False

def custom_example():
    """自定义示例"""
    
    print("\n" + "=" * 60)
    print("📋 自定义示例")
    print("=" * 60)
    
    print("💡 请输入您的文档需求（输入完成后按回车键）：")
    user_query = input("📝 ").strip()
    
    if not user_query:
        print("❌ 未输入有效内容")
        return False
    
    print(f"\n🚀 开始生成...")
    
    try:
        from main import DocumentGenerationPipeline
        
        pipeline = DocumentGenerationPipeline()
        result_files = pipeline.generate_document(
            user_query,
            output_dir="examples/custom"
        )
        
        print(f"\n✅ 文档生成完成！")
        print(f"📁 输出目录：{result_files['output_directory']}")
        print(f"📄 最终文档：{result_files['final_document']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        return False

def main():
    """主函数"""
    
    print("🌟 Gauz文档Agent - 快速示例演示")
    print("=" * 60)
    print("本脚本将演示如何使用系统生成不同类型的专业文档")
    print("=" * 60)
    
    print("\n请选择要运行的示例：")
    print("1. 文物影响评估报告")
    print("2. 环境影响评估报告")
    print("3. 技术方案书")
    print("4. 自定义需求")
    print("5. 运行所有示例")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请选择 (0-5): ").strip()
            
            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                example_1()
            elif choice == "2":
                example_2()
            elif choice == "3":
                example_3()
            elif choice == "4":
                custom_example()
            elif choice == "5":
                print("🚀 运行所有预设示例...")
                example_1()
                example_2()
                example_3()
                print("\n🎉 所有示例运行完成！")
                break
            else:
                print("❌ 请输入有效的选项 (0-5)")
                continue
                
            # 询问是否继续
            continue_choice = input("\n是否继续运行其他示例？(y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes', '是']:
                print("👋 再见！")
                break
                
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断操作")
            break
        except Exception as e:
            print(f"\n❌ 运行错误: {e}")
            continue
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 