import pandas as pd
import matplotlib.pyplot as plt
import os

def visualize():
    # 로그 파일 경로
    log_path = os.path.join(os.path.dirname(__file__), "training_log.csv")
    output_path = os.path.join(os.path.dirname(__file__), "training_result.png")

    if not os.path.exists(log_path):
        print(f"Error: 로그 파일을 찾을 수 없습니다: {log_path}")
        return

    # 데이터 로드
    df = pd.read_csv(log_path)

    # 그래프 설정
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Loss 그래프 (왼쪽 Y축)
    color = 'tab:red'
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss', color=color)
    ax1.plot(df['epoch'], df['loss'], color=color, marker='o', label='Training Loss')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Accuracy 그래프 (오른쪽 Y축)
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Accuracy', color=color)
    ax2.plot(df['epoch'], df['accuracy'], color=color, marker='s', label='Validation Accuracy')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.set_ylim(0, 1.05)

    # 제목 및 레이아웃
    plt.title('KoELECTRA Fine-tuning Training Progress')
    fig.tight_layout()
    
    # 그래프 저장
    plt.savefig(output_path)
    print(f"Visualization saved to: {output_path}")

if __name__ == "__main__":
    visualize()
