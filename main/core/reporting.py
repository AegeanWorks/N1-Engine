import json
import logging
import html as html_lib
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generates HTML reports from analysis results.
    """
    @staticmethod
    def generate_html_report(results: Dict[str, Any], filepath: str, intervention_name: str, metric_name: str) -> bool:
        """
        Generates an HTML report and saves it to the specified filepath.
        """
        intervention_name = html_lib.escape(intervention_name)
        metric_name = html_lib.escape(metric_name)

        try:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Analysis Report: {intervention_name}</title>
                <style>
                    body {{ font-family: sans-serif; margin: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    .section {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                    .warning {{ color: #d9534f; font-weight: bold; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <h1>Analysis Report</h1>
                <h2>Intervention: {intervention_name}</h2>
                <h3>Metric: {metric_name}</h3>

                <div class="section">
                    <h3>Overview</h3>
                    <p><b>Mean Difference:</b> {results['analysis'].get('mean_difference', 0):.2f}</p>
                    <p><b>Cohen's d:</b> {results['analysis'].get('cohens_d', 0):.2f}</p>
            """

            # Bootstrap CI
            if 'bootstrap_ci' in results['analysis']:
                ci = results['analysis']['bootstrap_ci']
                if ci and ci.get('lower') is not None:
                     html += f"<p><b>Bootstrap 95% CI:</b> [{ci.get('lower', 0):.2f}, {ci.get('upper', 0):.2f}]</p>"
                else:
                     html += f"<p><b>Bootstrap 95% CI:</b> N/A</p>"

            html += """
                </div>

                <div class="section">
                    <h3>Statistical Tests</h3>
                    <table>
                        <tr><th>Test</th><th>Statistic</th><th>p-value</th></tr>
            """

            t_test = results['analysis'].get('t_test', {})
            u_test = results['analysis'].get('mann_whitney_u', {})

            t_stat = t_test.get('statistic')
            t_p = t_test.get('p_value')
            u_stat = u_test.get('statistic')
            u_p = u_test.get('p_value')

            t_stat_str = f"{t_stat:.2f}" if t_stat is not None else "N/A"
            t_p_str = f"{t_p:.4f}" if t_p is not None else "N/A"
            u_stat_str = f"{u_stat:.2f}" if u_stat is not None else "N/A"
            u_p_str = f"{u_p:.4f}" if u_p is not None else "N/A"

            html += f"<tr><td>Welch's t-test</td><td>{t_stat_str}</td><td>{t_p_str}</td></tr>"
            html += f"<tr><td>Mann-Whitney U</td><td>{u_stat_str}</td><td>{u_p_str}</td></tr>"

            html += """
                    </table>
                </div>

                <div class="section">
                    <h3>Windows</h3>
                    <table>
                        <tr><th>Period</th><th>Dates</th><th>Count</th><th>Mean</th><th>Std Dev</th><th>Trend (Slope, p)</th></tr>
            """

            bw = results.get('baseline_window', {})
            iw = results.get('intervention_window', {})

            b_trend = bw.get('trend', {})
            i_trend = iw.get('trend', {})

            b_trend_str = f"{b_trend.get('slope', 0):.4f} (p={b_trend.get('p_value', 1):.4f})" if b_trend and b_trend.get('slope') is not None else "N/A"
            i_trend_str = f"{i_trend.get('slope', 0):.4f} (p={i_trend.get('p_value', 1):.4f})" if i_trend and i_trend.get('slope') is not None else "N/A"

            html += f"""
                        <tr>
                            <td>Baseline</td>
                            <td>{bw.get('start')} to {bw.get('end')}</td>
                            <td>{bw.get('count')}</td>
                            <td>{bw.get('mean', 0):.2f}</td>
                            <td>{bw.get('std', 0):.2f}</td>
                            <td>{b_trend_str}</td>
                        </tr>
                        <tr>
                            <td>Intervention</td>
                            <td>{iw.get('start')} to {iw.get('end')}</td>
                            <td>{iw.get('count')}</td>
                            <td>{iw.get('mean', 0):.2f}</td>
                            <td>{iw.get('std', 0):.2f}</td>
                            <td>{i_trend_str}</td>
                        </tr>
                    </table>
                </div>
            """

            if results.get('warnings'):
                html += """
                <div class="section">
                    <h3>Warnings</h3>
                    <ul>
                """
                for w in results['warnings']:
                    html += f"<li class='warning'>{html_lib.escape(str(w))}</li>"
                html += """
                    </ul>
                </div>
                """

            html += """
            </body>
            </html>
            """

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)

            return True
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return False
