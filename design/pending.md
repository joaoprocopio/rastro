# Pending screens

`index.excalidraw` redraws part of the `rsvp-api` front end. This file lists the parts that have no screen yet, so you can pick the next flow to draw. Each item names the `rsvp-api` pages under `src/pages/` that the screen replaces.

## Guest and client pages

The `/external` routes are the pages that the guest and the client see. No screen draws them:

- The form response, with the identity confirmation (`external/FormResponse`).
- The survey (`external/SurveyForm`).
- The invitation refusal (`external/GuestRecuseEvent`).
- The client panel (`external/ClientView`). The Clientes screen copies its link, but no screen draws the panel.

## Bulk imports

Each bulk import has a preview step and a result step, and the import jobs have a list and a detail page. No screen draws these flows:

- Guest upsert (`bulk-imports/guest-upsert`, `guests/excelImportPages/GuestImportPage`).
- Guest to group association (`bulk-imports/guest-group-association`).
- Blind copy association (`bulk-imports/bcc-association`).
- Fixed air origin association (`bulk-imports/fixed-air-origin-association`).
- Form field fill (`bulk-imports/fill-form-fields`).
- Flight creation (`bulk-imports/flight-create`).
- The import jobs list and detail (`importJobs`).

## Air operations

The Aéreo tab of Serviços draws only the flight list. These pages have no screen:

- The flight sheet validator (`flights/FlightSheetValidator`).
- Connections by origin (`flights/ConnectionsByOrigin`).
- Flights per guest (`flights/GuestsFlights`).
- The flight association workbench (`flights/FlightAssociationWorkbench`).
- The bulk ticket issue workbench (`flights/BulkIssueWorkbench`).
- The full ticket issue import (`flights/FullIssueImport`).
- Flight edit and delete (`flights/EditFlights`).
- Routes (`routes`).

## Letters after the send

The "preparar envio" screen ends at the send button. No screen shows what happens after the send:

- The send report, with the status, outcome, and reason of each recipient (`communication/CommunicationReports`).
- The send history (`communication/CommunicationHistory`).
- The letters tab on the guest page (`guests/GuestCommunications`).

## Blocks in the rich-text editor

The letter editor replaces the blocks with rich text, but the air, hotel, transfer, and guest flight blocks render guest data (`communication/blocks`). The design does not say how these blocks and their tags fit into the editor. This is a model decision before it is a screen, and `rsvp-api` ADR 0002 records why the guest flight block is its own block type.

## Event create and edit

The Visão geral note says that the properties are editable in place, but no screen draws the edit. These pages have no screen:

- Event creation (`events/RsvpCreate`).
- Event edit (`events/EventDataEdit`).
- The event document upload for ClickSign (`events/EventDocumentUpload`).

## Smaller pages

These pages are smaller, and no screen draws them:

- Form import, duplicate, field include, and group choice (`forms`).
- Hotel and transfer create and edit. The Serviços tabs exist, but their forms do not (`hotels`, `transfers`).
- Guest edit and history (`guests/GuestEditPage`, `guests/GuestHistory`).
- The task list and detail (`tasks`).
- The three manuals (`manuals`).
- Usuários and the inbox. The sidebar shows both, but neither has a screen.

## Missing states

Only the Eventos list and two login steps draw the empty, loading, and error states. The Workbench, Clientes, and Cliente screens have none.
