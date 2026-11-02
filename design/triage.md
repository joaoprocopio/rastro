# Design triage

This file lists the main decisions in each area file, so you can accept or change each one. Tick a box to accept the decision. Under **Change**, write what you want instead, and answer the open questions.

## externo.excalidraw

- [ ] One link per invite holds the confirmation, the refusal, and the survey.
- [ ] After an answer, the guest uses the same link to edit the answer or give up until the deadline.
- [ ] Each closed-link reason (expired, revoked, invalid) has its own message and an organizer contact.
- [ ] The client panel opens with an access code, is read-only, and exports a spreadsheet.

Open: Does the client see the CPF? Is the access code per client or per event?

**Change**:

## convidados.excalidraw

- [ ] The "Adicionar convidados" dialog accepts pasted rows and validates each row before it saves.
- [ ] A duplicate email offers Ignorar or Atualizar dados, and Ignorar is the default.
- [ ] Grupo, cópia oculta, origem do voo, and atributo are bulk actions on a selection.
- [ ] The operator edits every guest field in place, and only the email locks during a send.
- [ ] One Atividade feed replaces the history, the notes, and the letters tab.

Open: When a move puts a group over its limit, does the app block, warn, or allow it?

**Change**:

- edição de planilha dentro da UI sai, o sistema só ofere um validador. já tive essa ideia de ter um editor de planilha, mais isso tem implicações complexas demais.

- me arrependi

## servicos.excalidraw

- [ ] Two tabs, Voos and Passageiros, and the flight record replace the 8 air pages.
- [ ] The operator types each flight in "Novo voo", and no spreadsheet upload exists.
- [ ] Ticket numbers go into a grid that accepts pasted rows.
- [ ] "Marcar como emitido" has Desfazer.
- [ ] A transfer is an event route with its vehicles, so Rotas is not a separate page.

Open: Keep "Exportar passageiros"? Does the guest still pick a flight in the form?

**Change**:

## cartas.excalidraw

- [ ] "Enviar" opens a live report: Na fila, Enviando, then Concluído.
- [ ] Each failure reason is a plain sentence that says what to do.
- [ ] The resend to failures leaves "Sem confirmação" unticked, because the guest may get the letter twice.
- [ ] Air, hotel, and transfer data are cards that the operator inserts with "/", and a card hides when the guest has no data.
- [ ] One flight card with a "Mostrar" option replaces the two flight blocks of ADR 0002.

Open: Does the send notice go to the sender only, or to the whole team?

**Change**:

## evento.excalidraw

- [ ] "Novo evento" asks only for Nome, Data, and Cliente.
- [ ] One Responsável replaces the three coordinators, and the Tour House fields go away.
- [ ] Visão geral shows "Primeiros passos" until the setup is complete.
- [ ] The signature document (ClickSign) is a Termo property, and the operator picks which groups sign.

Open: Accept PDF for the Termo? Does Encerrado block guest answers?

**Change**:

## formularios.excalidraw

- [ ] One "Novo formulário" dialog starts a blank form or copies a form from any event.
- [ ] A copy creates new attributes in this event, so an edit never changes another event.
- [ ] Each group has one form, and the operator sets it from the form or from the group.
- [ ] The delete dialog names the groups, guests, and answers that the delete affects.

Open: Does "Editar atributo" change the attribute in every form of the event?

**Change**:

## workspace.excalidraw

- [ ] Guest requests (the legacy tasks) become Solicitações in the Caixa de entrada, and no tasks page exists.
- [ ] The inbox shows only items that need an action.
- [ ] Equipe invites by email and has no roles (ADR 0005).
- [ ] The manuals move to an external help center behind the "?" menu.

Open: Does a request go to the event Responsável only, or to the whole team? How long is an invite valid?

**Change**:

## estados.excalidraw

- [ ] Each empty state says what the page is for and offers the one action that fills it.
- [ ] A load error shows inline with "Tentar de novo", and the page keeps its sidebar and header.
- [ ] Lists scroll without pages of 10 rows.
- [ ] The operator can delete only a client with no events.

**Change**:
