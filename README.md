# Maya Knox 

**Maya Knox** é um componente personalizado avançado para o Home Assistant que fornece um sistema de alarme inteligente com foco em notificações ricas, automação de câmeras e uma interface visual premium.

![Maya Knox Card v1.1.8](www/security_robot.png)

## 🚀 Funcionalidades

*   **Sistema de Alarme Completo**: Suporte para estados Armado (Casa), Armado (Rua) e Desarmado.
*   **Notificações Ricas**: Envia notificações para o aplicativo do Home Assistant com **snapshots de câmeras** anexados automaticamente quando o alarme dispara.
*   **Gestão de Câmeras Internas**: Ativa automaticamente a detecção de movimento das câmeras internas apenas no modo **Armado (Rua)**, protegendo sua privacidade enquanto você está em casa.
*   **Configuração via UI**: Todo o setup é feito através da interface nativa do Home Assistant (Config Flow), sem necessidade de editar arquivos YAML.
*   **Monitoramento Inteligente**: Permite definir sensores de perímetro (externos) e sensores internos (incluindo câmeras).
*   **Cartão Lovelace Premium (v1.1.8)**: Inclui um cartão frontend animado com links sociais clicáveis, log de eventos e feedback visual pulsante.
*   **Anti-Cache Robusto**: Utiliza embedding Base64 para garantir que a imagem correta do ícone seja exibida, sem conflitos de cache do navegador.

## 📦 Instalação

### Via HACS (Recomendado)
1. Vá para **HACS** > **Integrações**.
2. Clique nos três pontos no canto superior direito e selecione **Repositórios Personalizados**.
3. Adicione a URL: `https://github.com/klausterra/maya_knox`
4. Selecione a categoria **Integração**.
5. Clique em **ADICIONAR**.
6. Procure por **Maya Knox** e instale.
7. Reinicie o Home Assistant.

### Manual
1. Copie a pasta `maya_knox` para o diretório `custom_components` do seu Home Assistant.
2. Reinicie o Home Assistant.

## ⚙️ Configuração

1. No Home Assistant, vá para **Configurações** > **Dispositivos e Serviços**.
2. Clique em **Adicionar Integração**.
3. Pesquise por **Maya Knox**.
4. Siga as instruções:
    *   **Sensores de Perímetro**: Portas/janelas e câmeras externas.
    *   **Sensores Internos**: Sensores de movimento e câmeras internas.
    *   **Automação Alexa**: Defina as frases e dispositivos para anúncios automáticos.
    *   **Armar Automático**: Sistema inteligente baseado na presença dos moradores (GPS).

## 🖥️ Cartão Frontend (Lovelace)

O cartão é instalado automaticamente como um recurso. Se precisar adicionar manualmente:
*   URL: `/maya_knox_www/maya-knox-card.js`
*   Tipo: `JavaScript Module`

### Exemplo de Configuração
```yaml
type: custom:maya-knox-card
entity: alarm_control_panel.maya_knox_portal
name: Central Maya Knox
```

## 🛠️ Arquitetura

O sistema é otimizado para performance e privacidade:
1. **Privacidade**: Câmeras internas têm detecção de movimento desativada automaticamente nos modos "Casa" ou "Desarmado".
2. **Confiabilidade**: Ícones embutidos em Base64 garantem visual consistente mesmo em redes instáveis ou com cache agressivo.
3. **Escalabilidade**: Suporta múltiplos serviços de notificação (Mobile App e Alexa) simultaneamente.

---
Desenvolvido por KlausTerra.
Instagran: [@mayahome.oficial](https://www.instagram.com/mayahome.oficial) | Web: [www.mayahome.ia.br](https://www.mayahome.ia.br)
