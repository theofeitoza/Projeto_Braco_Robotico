# --- IMPORTAÇÕES DE BIBLIOTECAS ---
import flet as ft  # A biblioteca principal para construir a interface gráfica
import time        # Usada para pausas (ex: time.sleep(2) e no 'PLAY MOVEMENTS')
import serial      # A biblioteca 'pyserial' é crucial para a comunicação com o Arduino

# --- CONFIGURAÇÃO DA CONEXÃO SERIAL ---
# Tenta estabelecer a conexão com o Arduino na porta 'COM5'
# ATENÇÃO: Você DEVE alterar 'COM5' para a porta COM correta em que o seu Arduino está conectado!
# (Você pode ver isso na IDE do Arduino ou no Gerenciador de Dispositivos do Windows)
# '9600' é o baud rate (velocidade), que deve ser o MESMO do 'Serial.begin(9600)' no Arduino.
try:
    ser = serial.Serial('COM5', 9600, timeout=1)
    # Pausa de 2 segundos para dar tempo ao Arduino de resetar e estabelecer a conexão
    time.sleep(2)
except serial.SerialException as e:
    print(f"Erro ao abrir a porta serial COM5: {e}")
    print("Verifique se o Arduino está conectado e se a porta COM está correTA.")
    # Em uma aplicação real, você poderia exibir isso em um pop-up de erro no Flet
    # Para este script, ele irá falhar se não conseguir conectar.
    ser = None # Define 'ser' como None se a conexão falhar

# --- FUNÇÃO PRINCIPAL DA APLICAÇÃO ---
# Esta função define toda a aplicação Flet.
def main(page: ft.Page):
    
    # Sai se a conexão serial não foi estabelecida
    if ser is None:
        page.add(ft.Text("Falha ao conectar ao Arduino. Verifique a porta COM e reinicie a aplicação.", color=ft.colors.RED_500, size=20))
        return

    page.title = "Controlador Braço Robótico"
    page.theme_mode = ft.ThemeMode.LIGHT # Define o tema claro

    # --- VARIÁVEIS DE ESTADO DA APLICAÇÃO ---
    # Armazenam os valores e estados atuais da interface
    
    # Valores iniciais dos sliders (Garra, Mão, Cotovelo, Ombro, Base)
    # Estes valores NÃO são enviados ao iniciar, apenas 'reset_positions' o faz.
    slider_values = [0, 90, 0, 0, 90] 
    
    # Valor do slot de memória selecionado (1, 2 ou 3). Começa no slot 1 (índice 0)
    moviment_value = 0 
    
    # Variável para guardar uma posição "salva" (SAVE POSITIONS)
    saved_properties = tuple(slider_values) 
    
    # Lista para armazenar os objetos 'Slider' e facilitar o acesso a eles
    sliders = [] 
    
    # Placeholder para o botão segmentado (será criado depois)
    segmented_button_moviment = None
    
    # Flag para interromper a reprodução (STOP MOVEMENT)
    stop_movement = False

    # --- DEFINIÇÃO DO BOTTOM SHEET (Pop-up inferior) ---
    # Usado para exibir mensagens de confirmação (ex: "Posição Salva")
    bottom_sheet = ft.BottomSheet(content=ft.Container(padding=20), open=False)
    page.overlay.append(bottom_sheet)

    # --- FUNÇÕES AUXILIARES E DE COMUNICAÇÃO ---

    def send_servo_value(servo_id, value):
        """
        Envia o comando de posição para um servo específico via serial.
        """
        if ser is None or not ser.is_open:
            print("Erro: Porta serial não está aberta.")
            return

        value = int(value) # Garante que o valor é um inteiro
        
        # Formata o comando: "ID,VALOR\n" (ex: "1,90\n")
        # O '\n' (nova linha) é importante, pois o Arduino usa 'Serial.parseInt()'
        # que processa os números quando encontra um caractere não numérico.
        command = f'{servo_id},{value}\n'
        
        # Codifica o comando para bytes (padrão utf-8) e o envia pela serial
        ser.write(command.encode('utf-8'))
        print(f"Enviando para servo {servo_id}: {value}")


    def get_values():
        """
        Retorna uma lista com os valores atuais de TODOS os sliders.
        """
        return [int(slider.value) for slider in sliders]


    # --- FUNÇÕES DE CALLBACK (HANDLERS DE EVENTOS) ---
    # Estas funções são chamadas quando o usuário interage com a GUI (clica em botões, move sliders)

    def handle_change(e):
        """
        Chamado QUANDO QUALQUER SLIDER é movido.
        """
        # 'e.control' é o slider que disparou o evento
        slider_id = e.control.data  # Pega o 'data' (ID 1-5) que definimos na criação do slider
        value = int(e.control.value) # Pega o valor atual do slider
        
        # Envia o comando para o Arduino em tempo real
        send_servo_value(slider_id, value)


    def handle_button_change2(e):
        """
        Chamado quando o usuário clica nos botões segmentados (1, 2, 3).
        """
        nonlocal moviment_value
        # 'e.data' contém o 'value' do segmento clicado (0, 1 ou 2)
        moviment_value = int(e.data)
        print(f"Slot de movimento selecionado: {moviment_value + 1}")
        page.update()


    def save_properties(e):
        """
        Chamado no clique curto do botão 'SAVE POSITIONS'.
        (Atualmente, faz o mesmo que o clique longo, mas sem o pop-up)
        """
        nonlocal saved_properties # 'nonlocal' permite modificar a variável do escopo 'main'
        slider_values = get_values()
        saved_properties = tuple(slider_values.copy())
        print(f"Propriedades salvas na memória: {saved_properties}")
        page.update()

    
    def reset_positions(e):
        """
        Chamado no clique do botão 'RESET POSITIONS'.
        """
        # Define uma posição padrão (Garra fechada, braço "em pé")
        slider_values = [0, 90, 0, 0, 90]
        
        # Atualiza a interface (sliders) e envia os valores para os servos
        for i, slider in enumerate(sliders):
            slider.value = slider_values[i]
            # Envia o valor para o servo correspondente (ID = i + 1)
            send_servo_value(i + 1, slider.value)  
        
        # Atualiza a página para refletir a mudança nos sliders
        page.update()


    def save_properties_long_press(e):
        """
        Chamado no clique longo (on_long_press) do 'SAVE POSITIONS'.
        """
        nonlocal saved_properties
        slider_values = get_values()
        saved_properties = tuple(slider_values.copy())
        print(f"Propriedades salvas (long press): {saved_properties}")
        # Mostra a mensagem de confirmação no bottom sheet
        show_bottom_sheet(f"Posições salvas na memória: {saved_properties}")
        page.update()

    
    def show_bottom_sheet(content_text):
        """
        Função helper para exibir o pop-up (Bottom Sheet) com uma mensagem.
        """
        bottom_sheet.content = ft.Container(ft.Text(content_text, size=16), padding=20)
        bottom_sheet.open = True
        page.update()

    
    # --- FUNÇÕES DE ARQUIVO (EXPORTAR / IMPORTAR / REPRODUZIR) ---
    
    def write_positions(e):
        """
        Chamado no clique do 'EXPORT POSITION'.
        Salva a POSIÇÃO ATUAL dos sliders no arquivo 'posicoes.txt',
        na linha selecionada pelo botão segmentado (1, 2 ou 3).
        """
        try:
            # Pega a linha selecionada (0, 1 ou 2)
            linha_escolhida = int(moviment_value) 
            
            # Lê o conteúdo atual do arquivo
            try:
                with open('posicoes.txt', 'r') as arquivo:
                    linhas = arquivo.readlines()
            except FileNotFoundError:
                # Se o arquivo não existir, cria uma lista vazia
                linhas = []

            # Garante que a lista 'linhas' tenha pelo menos 'linha_escolhida' + 1 elementos
            while len(linhas) <= linha_escolhida:
                linhas.append("\n") # Adiciona linhas em branco se necessário
            
            # Remove quebras de linha extras
            linhas = [linha.strip() for linha in linhas]

            # Obtém os valores atuais dos sliders
            slider_values = get_values()

            # Substitui a linha escolhida pelos valores atuais
            linhas[linha_escolhida] = f"{slider_values}"
            
            # Escreve a lista 'linhas' de volta no arquivo (sobrescrevendo o original)
            with open('posicoes.txt', 'w') as arquivo:
                for linha in linhas:
                    arquivo.write(f"{linha}\n") # Adiciona a quebra de linha de volta
            
            show_bottom_sheet(f'Valores exportados: {slider_values}, para a linha {linha_escolhida + 1}')
            print(f'Conteúdo escrito na linha {linha_escolhida + 1} em posicoes.txt.')
        
        except Exception as ex:
            show_bottom_sheet(f'Ocorreu um erro ao exportar: {ex}')


    def play_movements(e):
        """
        Chamado no clique do 'PLAY MOVEMENTS'.
        Lê TODAS as linhas do 'posicoes.txt' e executa os movimentos em sequência.
        """
        nonlocal stop_movement
        stop_movement = False # Reseta a flag de parada
        print("Iniciando reprodução de movimentos...")
        
        try:
            with open("posicoes.txt", 'r') as arquivo:
                linhas = arquivo.readlines()

            # Itera sobre cada linha (movimento) no arquivo
            for linha in linhas:
                # Verifica se o botão 'STOP' foi pressionado
                if stop_movement:
                    print("Reprodução interrompida pelo usuário.")
                    show_bottom_sheet("Reprodução interrompida.")
                    break # Sai do loop 'for'
                
                linha = linha.strip() # Limpa espaços em branco e \n
                if not linha:
                    continue # Pula linhas em branco
                
                print(f"Executando movimento: {linha}")
                
                # Processa a linha (ex: "[0, 90, 0, 0, 90]")
                sliders_str = linha.strip('[]') # Remove colchetes
                try:
                    # Converte a string "0, 90, ..." em uma lista de inteiros
                    slider_values = [int(float(value.strip())) for value in sliders_str.split(',')]
                except ValueError as ve:
                    print(f"Erro: Linha mal formatada no arquivo. {ve}")
                    continue # Pula esta linha
                
                # Atualiza a interface e envia os comandos para cada servo
                for i, slider in enumerate(sliders):
                    if i < len(slider_values):
                        slider.value = slider_values[i]
                        send_servo_value(i + 1, slider.value)
                
                page.update() # Atualiza a GUI para mostrar a nova posição dos sliders
                time.sleep(3) # Pausa por 3 segundos antes de ir para o próximo movimento

            if not stop_movement:
                show_bottom_sheet("Reprodução de movimentos concluída.")

        except FileNotFoundError:
            print('O arquivo posicoes.txt não foi encontrado.')
            show_bottom_sheet('Erro: Arquivo posicoes.txt não encontrado.')
        except Exception as ex:
            print(f'Ocorreu um erro durante a reprodução: {ex}')
            show_bottom_sheet(f'Ocorreu um erro: {ex}')


    def stop_movement_func(e):
        """
        Chamado no clique do 'STOP MOVEMENT'.
        Apenas ativa a flag 'stop_movement'.
        """
        nonlocal stop_movement
        stop_movement = True
        print('Comando de parada recebido.')


    def import_positions(e):
        """
        Chamado no clique do 'IMPORT POSITIONS'.
        Lê a UMA linha selecionada (1, 2 ou 3) do 'posicoes.txt' e
        move o braço para aquela posição.
        """
        try:
            linha_escolhida = int(moviment_value) # Pega o slot (0, 1 ou 2)
            
            with open('posicoes.txt', 'r') as arquivo:
                linhas = arquivo.readlines()

            if linha_escolhida >= len(linhas) or not linhas[linha_escolhida].strip():
                print(f"Erro: Não há dados na linha {linha_escolhida + 1}.")
                show_bottom_sheet(f"Erro: Não há dados na linha {linha_escolhida + 1}.")
                return

            # Processa a linha específica
            linha = linhas[linha_escolhida].strip()
            sliders_str = linha.strip('[]')
            slider_values = [int(float(value.strip())) for value in sliders_str.split(',')]
            
            # Atualiza os sliders (GUI) e envia os valores (Servos)
            for i, slider in enumerate(sliders):
                if i < len(slider_values):
                    slider.value = slider_values[i]
                    slider.update() # Atualiza o slider individualmente na UI
                    send_servo_value(i + 1, slider.value)

            page.update() # Confirma a atualização da página
            show_bottom_sheet(f"Posição da linha {linha_escolhida + 1} importada.")

        except FileNotFoundError:
            print('O arquivo posicoes.txt não foi encontrado.')
            show_bottom_sheet('Erro: Arquivo posicoes.txt não encontrado.')
        except Exception as ex:
            print(f'Ocorreu um erro ao importar: {ex}')
            show_bottom_sheet(f'Ocorreu um erro ao importar: {ex}')

    
    # --- CRIAÇÃO DOS ELEMENTOS DA GUI (SLIDERS) ---
    
    # Slider 0 (Garra)
    # min=0, max=90 (faixa de 90 graus)
    # data=1 (Este é o ID que será enviado para o Arduino)
    # on_change=handle_change (chama a função quando o valor muda)
    slider0 = ft.Slider(min=0, max=90, width=300, value=0, data=1, on_change=handle_change, label="{value}º", adaptive=True)
    
    # Slider 1 (Mão)
    slider1 = ft.Slider(min=0, max=180, width=300, value=90, data=2, on_change=handle_change, label="{value}º", adaptive=True)
    
    # Slider 2 (Cotovelo)
    slider2 = ft.Slider(min=0, max=180, width=300, value=0, data=3, on_change=handle_change, label="{value}º", adaptive=True)
    
    # Slider 3 (Ombro)
    slider3 = ft.Slider(min=0, max=180, width=300, value=0, data=4, on_change=handle_change, label="{value}º", adaptive=True)
    
    # Slider 4 (Base)
    slider4 = ft.Slider(min=0, max=180, width=300, value=90, data=5, on_change=handle_change, label="{value}º", adaptive=True)
    
    # Adiciona os sliders à lista 'sliders' (na ordem correta de ID 1 a 5)
    sliders = [slider0, slider1, slider2, slider3, slider4]

    
    def create_segmented_button_moviment():
        """
        Função que cria o botão segmentado (1, 2, 3) para selecionar o slot de memória.
        """
        nonlocal segmented_button_moviment
        segmented_button_moviment = ft.SegmentedButton(
            on_change=handle_button_change2, # Função chamada ao clicar
            selected={str(moviment_value)},  # Seleciona o valor inicial (0)
            allow_multiple_selection=False,
            segments=[
                # O 'value' é o que é enviado para o handler 'handle_button_change2'
                ft.Segment(value="0", label=ft.Text("1"), icon=ft.Icon(ft.icons.LOOKS_ONE)),
                ft.Segment(value="1", label=ft.Text("2"), icon=ft.Icon(ft.icons.LOOKS_TWO)),
                ft.Segment(value="2", label=ft.Text("3"), icon=ft.Icon(ft.icons.LOOKS_3)),
            ]
        )
        return segmented_button_moviment

    # --- MONTAGEM DA INTERFACE (LAYOUT) ---
    # Adiciona os elementos à página
    
    page.add(
        # --- LINHA 1: CABEÇALHO COM LOGOS ---
        ft.Container(
            ft.Row([
                ft.Image(src="imagens/ufcat3.png", width=200, height=100, fit=ft.ImageFit.CONTAIN),
                ft.Image(src="imagens/banner_ppgmo_23bbfad3fa.png", width=600, height=100, fit=ft.ImageFit.CONTAIN),
                ft.Image(src="imagens/imtec_logo-removebg-preview.png", width=200, height=100, fit=ft.ImageFit.CONTAIN),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND), # Distribui igualmente
            padding=10
        ),
        
        # --- LINHA 2: CONTEÚDO PRINCIPAL ---
        ft.Container(
            ft.Row([
                
                # --- COLUNA 1: BOTÕES DE AÇÃO (Esquerda) ---
                ft.Column([
                    ft.ElevatedButton(text="SAVE POSITIONS", on_click=save_properties, on_long_press=save_properties_long_press, width=250, height=70, style=ft.ButtonStyle(bgcolor=ft.colors.BLACK, color=ft.colors.WHITE)),
                    ft.ElevatedButton(text="PLAY MOVEMENTS", on_click=play_movements, width=250, height=70, style=ft.ButtonStyle(bgcolor=ft.colors.BLACK, color=ft.colors.WHITE)),
                    ft.ElevatedButton(text="STOP MOVEMENT", on_click=stop_movement_func, width=250, height=70, style=ft.ButtonStyle(bgcolor=ft.colors.RED_700, color=ft.colors.WHITE)), # Botão STOP em vermelho
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, height=400),
                
                # --- COLUNA 2: IMAGEM DO BRAÇO (Centro-Esquerda) ---
                ft.Column([
                    ft.Image(src="imagens/braço.png", width=300, height=300, fit=ft.ImageFit.CONTAIN),
                ], alignment=ft.MainAxisAlignment.CENTER, height=400),
                
                # --- COLUNA 3: SLIDERS (Centro-Direita) ---
                ft.Column([
                    ft.Text('Garra (ID 1)', text_align=ft.TextAlign.CENTER),
                    ft.Row([slider0]),
                    ft.Text('Mão (ID 2)'),
                    ft.Row([slider1]),
                    ft.Text('Cotovelo (ID 3)'),
                    ft.Row([slider2]),
                    ft.Text('Ombro (ID 4)'),
                    ft.Row([slider3]),
                    ft.Text('Base (ID 5)'),
                    ft.Row([slider4]),
                    ft.Row([create_segmented_button_moviment()], alignment=ft.MainAxisAlignment.CENTER) # Botões 1,2,3
                ], alignment=ft.MainAxisAlignment.CENTER, height=600),
                
                # --- COLUNA 4: BOTÕES DE ARQUIVO (Direita) ---
                ft.Column([
                    ft.ElevatedButton(text="EXPORT POSITION", on_click=write_positions, width=250, height=70, style=ft.ButtonStyle(bgcolor=ft.colors.BLACK, color=ft.colors.WHITE)),
                    ft.ElevatedButton(text="IMPORT POSITIONS", on_click=import_positions, width=250, height=70, style=ft.ButtonStyle(bgcolor=ft.colors.BLACK, color=ft.colors.WHITE)),
                    ft.ElevatedButton(text="RESET POSITIONS", on_click=reset_positions, width=250, height=70, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_GREY, color=ft.colors.WHITE)),
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, height=400),
                
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND), # Distribui as colunas
            padding=20,
            expand=True
        )
    )

# --- INICIALIZAÇÃO DA APLICAÇÃO FLET ---
# Verifica se a conexão serial foi bem-sucedida antes de tentar iniciar o app
if __name__ == "__main__":
    ft.app(target=main)
    
    # --- FECHAMENTO DA PORTA SERIAL ---
    # Quando o usuário fechar a janela do Flet, o 'ft.app' termina
    # e o código abaixo é executado.
    if ser is not None and ser.is_open:
        ser.close()
        print("Porta serial fechada.")
