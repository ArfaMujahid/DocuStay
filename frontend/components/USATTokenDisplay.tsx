
import React from 'react';
import { Card } from './UI';
import { USATToken } from '../services/tokenService';

interface Props {
  token: USATToken;
}

export const USATTokenDisplay: React.FC<Props> = ({ token }) => {
  return (
    <Card className="max-w-md w-full bg-[#111827] border-blue-500/30 overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.4)]">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-center">
        <h3 className="text-white font-black uppercase tracking-[0.2em] text-sm">Stay Authorization Pass</h3>
      </div>
      
      <div className="p-8 space-y-8">
        <div className="flex justify-between items-center">
           <div className="bg-white p-3 rounded-2xl shadow-xl">
             <img src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${token.tokenId}`} alt="Token QR" className="w-24 h-24" />
           </div>
           <div className="text-right">
             <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">Token ID</p>
             <p className="text-white font-mono font-bold text-lg">{token.tokenId}</p>
             <div className="mt-2 inline-flex items-center gap-2 px-2 py-1 rounded-md bg-green-500/10 text-green-400 border border-green-500/20 text-[10px] font-black uppercase">
               <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
               {token.status}
             </div>
           </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">Guest</p>
            <p className="text-white font-bold text-sm">{token.guestName}</p>
          </div>
          <div>
            <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">Expires</p>
            <p className="text-white font-bold text-sm">{new Date(token.expiresAt).toLocaleDateString()}</p>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-6 space-y-4">
           <div className="flex items-center gap-3 text-sm text-gray-400">
             <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path></svg>
             <span>Utility Access: USE ONLY</span>
           </div>
           <p className="text-[10px] text-gray-600 italic leading-relaxed">This token is a cryptographically signed authorization protocol. It does not establish residency or tenancy rights under any jurisdiction.</p>
        </div>
      </div>

      <div className="bg-black/40 p-4 border-t border-gray-800 flex justify-center">
         <div className="text-[9px] font-black text-gray-700 uppercase tracking-widest">Signed by DocuStay HUAP Engine v2.0</div>
      </div>
    </Card>
  );
};
