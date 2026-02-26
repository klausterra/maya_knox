# Maya Knox 

**Maya Knox** é um componente personalizado avançado para o Home Assistant que fornece um sistema de alarme inteligente com foco em notificações ricas e uma interface visual amigável.

![Maya Knox Logo](assets/logo.png)

##  Funcionalidades

*   **Sistema de Alarme Completo**: Suporte para estados Armado (Casa), Armado (Fora) e Desarmado.
*   **Notificações Ricas**: Envia notificações para o aplicativo do Home Assistant com **snapshots de câmeras** anexados automaticamente quando o alarme dispara.
*   **Configuração via UI**: Todo o setup é feito através da interface nativa do Home Assistant (Config Flow), sem necessidade de editar arquivos YAML.
*   **Monitoramento Inteligente**: Permite definir sensores de perímetro (externos) e sensores internos.
*   **Cartão Lovelace Personalizado**: Inclui um cartão frontend animado que muda de cor e pulsa quando o alarme está disparado.

##  Instalação

1.  Copie a pasta maya_knox para o diretório custom_components do seu Home Assistant.
2.  Reinicie o Home Assistant.

##  Configuração

1.  No Home Assistant, vá para **Configurações** > **Dispositivos e Serviços**.
2.  Clique em **Adicionar Integração**.
3.  Pesquise por **Maya Knox**.
4.  Preencha o formulário de configuração:
    *   **Sensores de Perímetro**: Selecione os sensores de porta/janela ou câmeras que monitoram a área externa.
    *   **Sensores Internos**: Selecione sensores de movimento internos.
    *   **Moradores**: Selecione as pessoas para rastreamento de presença.
    *   **Ativar Armar Automático**: Se ativado, o sistema armará automaticamente (Ausente) quando todos os moradores saírem e desarmará quando o primeiro chegar.

## Cartão Frontend (Lovelace)

O componente inclui um cartão personalizado para exibir o status do alarme.

### Adicionando o Recurso

O recurso deve ser adicionado automaticamente. Se não for, adicione manualmente em **Painéis** > **Três pontos** > **Recursos**:
*   URL: /maya_knox_www/maya-knox-card.js
*   Tipo: JavaScript Module

### Exemplo de Uso no Dashboard

`yaml
type: custom:maya-knox-card
entity: alarm_control_panel.maya_knox_alarm
name: Alarme Principal
`

## Como Funciona (Arquitetura)

O sistema é composto por três partes principais que interagem entre si:

### 1. Painel de Controle (larm_control_panel.py)
É o "cérebro" do sistema. Ele gerencia os estados do alarme (Armado/Desarmado/Disparado).
*   **Diferencial**: Quando o alarme dispara (TRIGGERED), ele verifica se há câmeras configuradas na lista de "Sensores de Perímetro". Se houver, ele captura uma imagem e a envia junto com a notificação de alerta para o seu celular.

### 2. Fluxo de Configuração (config_flow.py)
Gerencia a interface de configuração inicial. Ele coleta as listas de sensores e preferências do usuário e as armazena para uso pelo Painel de Controle.

### 3. Interface Visual (www/maya-knox-card.js)
Um cartão personalizado escrito em JavaScript.
*   **Visual**: Exibe o ícone do robô Maya Knox.
*   **Feedback Visual**:
    *    **Verde**: Desarmado.
    *    **Vermelho**: Armado.
    *    **Laranja Pulsante**: Disparado (Alerta Visual).
*   **Interação**: Ao clicar no cartão, ele abre o diálogo de "Mais Informações" do alarme para permitir armar/desarmar.

---
Desenvolvido por KlausTerra.
