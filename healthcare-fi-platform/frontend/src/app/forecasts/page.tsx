import { redirect } from 'next/navigation';

// /forecasts is a dead duplicate route — redirect to the real forecasting page
export default function ForecastsRedirect() {
  redirect('/forecasting');
}
