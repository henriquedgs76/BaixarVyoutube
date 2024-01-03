import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from pytube import YouTube

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class DownloadThread(QThread):
    update_progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, video_url, pasta_destino, formato, resolucao):
        super().__init__()
        self.video_url = video_url
        self.pasta_destino = pasta_destino
        self.formato = formato
        self.resolucao = resolucao

    def run(self):
        try:
            yt = YouTube(self.video_url, on_progress_callback=self.progress_callback)
            
            if self.formato == 'Vídeo':
                stream = yt.streams.filter(res=self.resolucao, file_extension='mp4').first()
                if not stream:
                    QMessageBox.warning(None, 'Aviso', 'Resolução selecionada não disponível para este vídeo.')
                    return
            elif self.formato == 'Áudio':
                stream = yt.streams.filter(only_audio=True).first()
            elif self.formato == 'Apenas Áudio':
                stream = yt.streams.filter(only_audio=True).first()
                self.pasta_destino = self.pasta_destino + '/audio_only'
            else:
                QMessageBox.warning(None, 'Aviso', 'Formato selecionado não é suportado.')
                return
            
            stream.download(output_path=self.pasta_destino)
        except Exception as e:
            QMessageBox.warning(None, 'Erro', f'Ocorreu um erro: {str(e)}')
        finally:
            self.finished.emit()

    def progress_callback(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        progress_percentage = int((bytes_downloaded / total_size) * 100)
        self.update_progress.emit(progress_percentage)

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Baixar Vídeo/Aúdio Youtube')

        self.label_url = QLabel('Digite a URL do vídeo:')
        self.entrada_url = QLineEdit()

        self.label_formato = QLabel('Selecione o formato que deseja:')
        self.combo_formato = QComboBox()
        self.combo_formato.addItems(['Vídeo', 'Áudio', 'Apenas Áudio'])

        self.label_resolucao = QLabel('Selecione a resolução:')
        self.combo_resolucao = QComboBox()
        self.combo_resolucao.addItems(['1080p', '720p', '480p', '360p', '240p', '144p'])

        self.label_destino = QLabel('Selecione a pasta de destino:')
        self.entrada_destino = QLineEdit()
        self.botao_selecionar_destino = QPushButton('Selecionar Pasta para Salvar')
        self.botao_selecionar_destino.clicked.connect(self.selecionar_pasta_destino)

        self.botao_download = QPushButton('Clique aqui para começar o Download.')
        self.botao_download.clicked.connect(self.baixar_video)

        self.fig, self.ax = plt.subplots(figsize=(5, 2))
        self.canvas = FigureCanvas(self.fig)
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 1)
        self.ax.set_title('Progresso do Download')
        self.ax.set_xlabel('Progresso (%)')
        self.ax.set_ylabel('')

        layout = QVBoxLayout()
        layout.addWidget(self.label_url)
        layout.addWidget(self.entrada_url)
        layout.addWidget(self.label_formato)
        layout.addWidget(self.combo_formato)
        layout.addWidget(self.label_resolucao)
        layout.addWidget(self.combo_resolucao)
        layout.addWidget(self.label_destino)
        layout.addWidget(self.entrada_destino)
        layout.addWidget(self.botao_selecionar_destino)
        layout.addWidget(self.botao_download)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        self.thread_download = None

    def baixar_video(self):
        url_video = self.entrada_url.text()
        formato_selecionado = self.combo_formato.currentText()
        resolucao_selecionada = self.combo_resolucao.currentText()

        pasta_destino = self.entrada_destino.text()
        if not pasta_destino:
            QMessageBox.warning(None, 'Aviso', 'Selecione uma pasta de destino válida.')
            return

        if self.thread_download and self.thread_download.isRunning():
            self.thread_download.finished.connect(self.lidar_thread_finalizada)
            self.thread_download.quit()
        else:
            self.iniciar_thread_download(url_video, pasta_destino, formato_selecionado, resolucao_selecionada)

    def iniciar_thread_download(self, url_video, pasta_destino, formato_selecionado, resolucao_selecionada):
        self.thread_download = DownloadThread(url_video, pasta_destino, formato_selecionado, resolucao_selecionada)
        self.thread_download.update_progress.connect(self.atualizar_progresso)
        self.thread_download.finished.connect(self.lidar_thread_finalizada)
        self.thread_download.start()

    def atualizar_progresso(self, progresso):
        self.ax.clear()
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 1)
        self.ax.set_title('Progresso do Download')
        self.ax.set_xlabel('Progresso (%)')
        self.ax.set_ylabel('')
        self.ax.bar(0, 1, width=progresso, align='edge', color='red', alpha=0.9)
        self.canvas.draw()

    def lidar_thread_finalizada(self):
        self.thread_download.finished.disconnect(self.lidar_thread_finalizada)
        self.thread_download = None

    def selecionar_pasta_destino(self):
        pasta_destino = QFileDialog.getExistingDirectory(self, 'Selecione a pasta de destino')
        if pasta_destino:
            self.entrada_destino.setText(pasta_destino)

    def closeEvent(self, event):
        if self.thread_download and self.thread_download.isRunning():
            self.thread_download.finished.connect(self.lidar_thread_finalizada)
            self.thread_download.quit()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    janela = YouTubeDownloader()
    janela.show()
    sys.exit(app.exec_())
