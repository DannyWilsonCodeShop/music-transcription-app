import { type ClientSchema, a, defineData } from '@aws-amplify/backend';

/*== MUSIC TRANSCRIPTION SCHEMA ==========================================
Schema for music transcription jobs with lyrics and chord progressions
=========================================================================*/
const schema = a.schema({
  TranscriptionJob: a
    .model({
      id: a.id().required(),
      status: a.enum(['pending', 'processing', 'completed', 'failed']),
      audioUrl: a.string(),
      youtubeUrl: a.string(),
      title: a.string(),
      artist: a.string(),
      lyrics: a.string(),
      chords: a.json(),
      createdAt: a.datetime(),
      updatedAt: a.datetime(),
      userId: a.string(),
    })
    .authorization((allow) => [
      allow.owner(),
      allow.guest().to(['create', 'read'])
    ]),
  
  User: a
    .model({
      id: a.id().required(),
      email: a.string(),
      name: a.string(),
      createdAt: a.datetime(),
    })
    .authorization((allow) => [allow.owner()]),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: 'identityPool',
  },
});

/*== STEP 2 ===============================================================
Go to your frontend source code. From your client-side code, generate a
Data client to make CRUDL requests to your table. (THIS SNIPPET WILL ONLY
WORK IN THE FRONTEND CODE FILE.)

Using JavaScript or Next.js React Server Components, Middleware, Server 
Actions or Pages Router? Review how to generate Data clients for those use
cases: https://docs.amplify.aws/gen2/build-a-backend/data/connect-to-API/
=========================================================================*/

/*
"use client"
import { generateClient } from "aws-amplify/data";
import type { Schema } from "@/amplify/data/resource";

const client = generateClient<Schema>() // use this Data client for CRUDL requests
*/

/*== STEP 3 ===============================================================
Fetch records from the database and use them in your frontend component.
(THIS SNIPPET WILL ONLY WORK IN THE FRONTEND CODE FILE.)
=========================================================================*/

/* For example, in a React component, you can use this snippet in your
  function's RETURN statement */
// const { data: todos } = await client.models.Todo.list()

// return <ul>{todos.map(todo => <li key={todo.id}>{todo.content}</li>)}</ul>
