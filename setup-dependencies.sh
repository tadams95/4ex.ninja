#!/bin/bash
cd 4ex.ninja-frontend
npm install --save prisma @prisma/client bcryptjs
npx prisma generate
